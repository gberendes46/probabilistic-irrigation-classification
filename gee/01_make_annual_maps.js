/**** 
 * 01_make_annual_maps
 *
 * Template: Probabilistic irrigation classification in Google Earth Engine (GEE)
 *
 * You should edit ONLY the "USER SETTINGS" section. Everything else is workflow logic.
 *
 * Workflow summary:
 *  1) For each region-year:
 *     - Build a grassland LST CDF per usable Landsat scene
 *     - Convert corn LST to a pixelwise likelihood image using that CDF
 *     - Combine likelihoods across scenes (product in log-space)
 *     - Use a prior on irrigation fraction p (Beta distribution)
 *     - Compute posterior(p | data) on a grid
 *     - Marginalize over p to get per-pixel irrigation probability ("posterior_mean")
 *  2) Export maps (posterior_mean + diagnostics) to an EE Asset collection you specify
 *
 * Notes:
 *  - This script assumes you have a county-year prior table OR some other way to define
 *    an irrigation-fraction prior median (0–1). Replace getRegionYearIrrFraction() as needed.
 *  - This template uses TIGER counties by default, but you can swap in any FeatureCollection.
 ****/
 
 /**
 * Paper defaults:
 *   PRIOR_STRENGTH_S = 15
 *   DELTA_T_OFFSET_C = 1.66
 *   SCENE_START_MMDD = '07-01'
 *   SCENE_END_MMDD   = '08-31'
 *   MIN_COVERAGE_FRACTION = 0.5
 */


/* =============================================================================
 * USER SETTINGS (EDIT THESE)
 * =============================================================================
 */

// (1) Regions
// Option A (recommended general mode): bring your own FeatureCollection of regions.
//  - Must contain a geometry per feature
//  - Must contain a string id/name field used for exports (e.g., 'NAME' or 'id')
var REGIONS_FC = null;
// Example:
// var REGIONS_FC = ee.FeatureCollection('users/YOUR_USERNAME/your_regions')
//   .select(['id']);   // where 'id' is a unique string per region

// Option B (example mode): TIGER counties for state(s). If REGIONS_FC is null, TIGER mode is used.
var STATES = ['INSERT_STATE_NAME_HERE'];  // Example: ['NEBRASKA','KANSAS']

// (2) Years
var YEAR_STRINGS = ['INSERT_YEAR_HERE'];  // Example: ['2006','2007','2008']
var YEARS_INT    = [0000];               // Example: [2006,2007,2008]

// (3) Seasonal window for Landsat scenes (MM-DD)
var SCENE_START_MMDD = '07-01';
var SCENE_END_MMDD   = '08-31';

// (4) Export destination (YOU MUST SET THIS)
// Put the Asset *collection* you want to export into.
// Example: 'projects/ee-gfb46/assets/annual_maps'
var OUTPUT_ASSET_COLLECTION = 'INSERT_YOUR_ASSET_COLLECTION_PATH_HERE';

// (5) Prior information source (YOU MUST SET OR REPLACE getRegionYearIrrFraction())
// Option: set a FeatureCollection asset that has region-year prior info.
var IRR_PRIOR_TABLE = ee.FeatureCollection('INSERT_YOUR_PRIOR_TABLE_ASSET_PATH_HERE');

// Expected fields IF you use the default getRegionYearIrrFraction():
//  - State (string, uppercase)   [only needed for TIGER mode]
//  - County (string, uppercase)  [only needed for TIGER mode]
//  - Year (int)
//  - Percent Irrigated (0–100)

// (6) Prior strength (bigger = tighter prior around the median)
var PRIOR_STRENGTH_S = ee.Number('INSERT_YOUR_PRIOR_STRENGTH_HERE');

// (7) Posterior integration grid over p
var P_MIN = 0.01;
var P_MAX = 0.99;
var P_STEP = 0.01;

// (8) CDL crop codes (edit if needed)
var CDL_CORN_CODE  = 1;
var CDL_GRASS_CODE = 176;

// (9) Optional binary classification threshold
var POSTERIOR_THRESHOLD = 0.5;

// (10) Landsat satellites to include
var SATELLITES = ['L5', 'L7', 'L8', 'L9'];

// (11) Compute
var SCALE_M = 30;
var MAX_PIX = 1e13;

// (12) External LST modules (kept as-is; these are public modules)
var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');
var BBE = require('users/sofiaermida/landsat_smw_lst:modules/broadband_emiss.js');
var USE_NDVI = false;

// (13) Thermal offset correction (°C) applied to crop LST before comparison to grassland CDF.
// Example used in the paper: 1.66
var DELTA_T_OFFSET_C = 0;  // INSERT_YOUR_VALUE_HERE

// (14) Minimum fraction of region that must be valid (cloud-free) for a scene to be "usable"
var MIN_COVERAGE_FRACTION = 0.5;

/* =============================================================================
 * HELPER FUNCTIONS
 * =============================================================================
 */

function normalizeName(name) {
  return ee.String(name).upper();
}

// Example FIPS mapping for TIGER mode. Add as needed.
function getStateFP(stateName) {
  var stateFIPS = {
    'NEBRASKA': '31'
    // Add more:
    // 'KANSAS': '20',
  };
  return stateFIPS[stateName.toUpperCase()];
}

/**
 * Build a grassland CDF from an LST image (single band 'LST').
 * Returns a dictionary mapping integer LST (rounded) -> cumulative probability.
 */
function buildGrasslandCdfDict(lstGrassImage, geometry) {
  var hist = lstGrassImage.reduceRegion({
    reducer: ee.Reducer.histogram(100),
    geometry: geometry,
    scale: SCALE_M,
    maxPixels: MAX_PIX
  });

  var histDict = ee.Dictionary(hist.get('LST'));
  var bucketMeans = ee.List(histDict.get('bucketMeans'));
  var counts = ee.List(histDict.get('histogram'));

  var cumCounts = ee.Array(counts).accum({axis: 0});
  var total = cumCounts.get([-1]);
  var cumProb = cumCounts.divide(total);

  var array = ee.Array.cat([bucketMeans, cumProb], 1);

  var fc = ee.FeatureCollection(array.toList().map(function(row) {
    row = ee.List(row);
    return ee.Feature(null, { LST: row.get(0), probability: row.get(1) });
  }));

  var cdfList = fc.map(function(f) {
    return f.set('dict', f.toDictionary(['LST','probability']));
  }).aggregate_array('dict');

  var cdfDict = ee.Dictionary(cdfList.iterate(function(item, result) {
    item = ee.Dictionary(item);
    var lst = ee.Number(item.get('LST')).round();
    var p = ee.Number(item.get('probability'));
    return ee.Dictionary(result).set(lst, p);
  }, ee.Dictionary({})));

  return cdfDict;
}

/**
 * Convert corn LST to pixelwise likelihood using a grassland CDF dictionary.
 */
function likelihoodFromCdfDict(lstCornImage, cdfDict) {
  var cdfKeys = cdfDict.keys().map(function(k){ return ee.Number.parse(k); });
  var cdfVals = cdfDict.values().map(function(v){ return ee.Number.parse(v); });

  var lstShifted = ee.Image(lstCornImage).add(DELTA_T_OFFSET_C).round();
  
  var minLST = ee.Number(cdfKeys.reduce(ee.Reducer.min()));
  var maxLST = ee.Number(cdfKeys.reduce(ee.Reducer.max()));

  var maskLow = lstShifted.lt(minLST);
  var maskHigh = lstShifted.gt(maxLST);

  var likelihood = lstShifted.remap({
    from: cdfKeys,
    to: cdfVals,
    defaultValue: 0
  });

  return likelihood.where(maskLow, 0).where(maskHigh, 1);
}

/**
 * Merge Landsat LST across satellites for a date window and geometry.
 * Returns ImageCollection with band 'LST'.
 */
function getMergedLandsatLST(dateStart, dateEnd, geometry) {
  var merged = ee.ImageCollection([]);
  SATELLITES.forEach(function(sat) {
    var coll = LandsatLST.collection(sat, dateStart, dateEnd, geometry, USE_NDVI);
    coll = coll.map(BBE.addBand(true));
    merged = merged.merge(coll.map(function(img){ return img.select('LST').rename('LST'); }));
  });
  return merged;
}

/**
 * Filter scenes by requiring >= fractionThreshold of pixels in the geometry to be valid.
 */
function filterByCoverage(lstCollection, geometry, fractionThreshold) {
  var totalPix = ee.Number(
    ee.Image.constant(1).reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: geometry,
      crs: 'EPSG:4326',
      scale: SCALE_M,
      maxPixels: 12e12
    }).values().get(0)
  );

  var threshold = totalPix.multiply(fractionThreshold);

  var withCounts = lstCollection.map(function(img) {
    var count = ee.Number(img.select('LST').reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: geometry,
      crs: 'EPSG:4326',
      scale: SCALE_M,
      maxPixels: 12e12
    }).get('LST'));
    return img.set('count', count);
  });

  return withCounts.filter(ee.Filter.gt('count', threshold));
}

function betaParamsFromMedian(median, S) {
  var oneThird = ee.Number(1).divide(3);
  var twoThird = ee.Number(2).divide(3);
  var alphaGuess = ee.Number(median).multiply(S.subtract(twoThird)).add(oneThird);
  var eps = ee.Number(1.001);
  var alpha = alphaGuess.max(eps).min(S.subtract(eps));
  var beta  = S.subtract(alpha);
  return ee.Dictionary({alpha: alpha, beta: beta});
}

function betaPdfUnnorm(p, alpha, beta) {
  p = ee.Number(p);
  return p.pow(alpha.subtract(1)).multiply(ee.Number(1).subtract(p).pow(beta.subtract(1)));
}


/* =============================================================================
 * PRIOR LOOKUP (CUSTOMIZE THIS FOR YOUR PROJECT)
 * =============================================================================
 *
 * This function returns the *prior median irrigation fraction* in [0,1] for a region-year.
 * Replace its internals to match how YOUR prior information is stored.
 *
 * Template assumes TIGER counties and a table with State/County/Year/Percent Irrigated.
 */
function getRegionYearIrrFraction(stateUpper, regionNameUpper, yearInt) {

  // If you do NOT have a prior table, you could:
  //  - return a constant like 0.5
  //  - or compute a prior from an external dataset
  //  - or set state-level medians
  //
  // Example constant prior:
  // return ee.Number(0.5);

  var filtered = IRR_PRIOR_TABLE.filter(ee.Filter.and(
    ee.Filter.eq('State', stateUpper),
    ee.Filter.eq('County', regionNameUpper),
    ee.Filter.eq('Year', yearInt)
  ));

  var first = filtered.first();
  var perc = ee.Number(ee.Algorithms.If(
    first,
    ee.Feature(first).get('Percent Irrigated'),
    0
  ));

  return perc.divide(100);
}


/* =============================================================================
 * MAIN
 * =============================================================================
 */

var P_VALUES = ee.List.sequence(P_MIN, P_MAX, P_STEP);

if (REGIONS_FC !== null) {
  runOnCustomRegions(REGIONS_FC);
} else {
  runOnTigerCounties();
}


/**
 * Mode 1: Custom region FeatureCollection (you supply REGIONS_FC)
 * Requirements:
 *  - each feature has geometry
 *  - each feature has an id/name property you choose below
 */
function runOnCustomRegions(regionsFC) {

  // INSERT YOUR REGION ID FIELD HERE:
  var REGION_ID_FIELD = 'INSERT_REGION_ID_FIELD_HERE'; // Example: 'id' or 'NAME'

  regionsFC.aggregate_array(REGION_ID_FIELD).evaluate(function(ids) {
    ids.forEach(function(id) {
      var feature = regionsFC.filter(ee.Filter.eq(REGION_ID_FIELD, id)).first();
      var geometry = ee.Feature(feature).geometry();
      var regionName = String(id).toUpperCase();

      for (var i = 0; i < YEAR_STRINGS.length; i++) {
        runRegionYear({
          geometry: geometry,
          regionNameUpper: regionName,
          stateUpper: null,          // not used unless your prior needs it
          yearStr: YEAR_STRINGS[i],
          yearInt: YEARS_INT[i]
        });
      }
    });
  });
}


/**
 * Mode 2: TIGER counties for selected STATES
 */
function runOnTigerCounties() {

  STATES.forEach(function(stateName) {
    var stateUpper = stateName.toUpperCase();
    print('Processing state:', stateUpper);

    var counties = ee.FeatureCollection('TIGER/2016/Counties')
      .filter(ee.Filter.eq('STATEFP', getStateFP(stateUpper)));

    var countyNames = counties.aggregate_array('NAME').getInfo().map(function(n){ return n.toUpperCase(); });
    var geoids = counties.aggregate_array('GEOID').getInfo();

    for (var c = 0; c < countyNames.length; c++) {
      var countyNameUpper = countyNames[c];
      var countyGEOID = geoids[c];

      var geometry = ee.FeatureCollection('TIGER/2016/Counties')
        .filter(ee.Filter.eq('GEOID', countyGEOID))
        .geometry();

      for (var i = 0; i < YEAR_STRINGS.length; i++) {
        runRegionYear({
          geometry: geometry,
          regionNameUpper: countyNameUpper,
          stateUpper: stateUpper,
          yearStr: YEAR_STRINGS[i],
          yearInt: YEARS_INT[i]
        });
      }
    }
  });
}


/**
 * Core region-year pipeline. This is the “main method”.
 */
function runRegionYear(args) {

  var geometry = args.geometry;
  var regionNameUpper = args.regionNameUpper;
  var stateUpper = args.stateUpper; // may be null in custom-region mode
  var yearStr = args.yearStr;
  var yearInt = args.yearInt;

  // (A) Date windows
  var yearStart = yearStr + '-01-01';
  var yearEnd   = yearStr + '-12-31';
  var sceneStart = yearStr + '-' + SCENE_START_MMDD;
  var sceneEnd   = yearStr + '-' + SCENE_END_MMDD;

  // (B) CDL masks (corn + grassland)
  var cdl = ee.ImageCollection('USDA/NASS/CDL')
    .filter(ee.Filter.date(yearStart, yearEnd))
    .first()
    .select('cropland');

  var cornMask  = cdl.eq(CDL_CORN_CODE).selfMask();
  var grassMask = cdl.eq(CDL_GRASS_CODE).selfMask();

  // (C) Landsat LST collection, coverage-filtered
  var mergedLST = getMergedLandsatLST(sceneStart, sceneEnd, geometry);
  var usable = filterByCoverage(mergedLST, geometry, MIN_COVERAGE_FRACTION);

  var nImages = usable.size().getInfo();
  if (nImages === 0) {
    print('No usable scenes for', regionNameUpper, yearStr, '- skipping.');
    return;
  }

  var imageList = usable.toList(nImages);

  // (D) Stack per-scene likelihoods
  var likelihoodStack = ee.Image([]);

  for (var id = 0; id < nImages; id++) {
    var img = ee.Image(imageList.get(id));

    var lstCorn  = img.updateMask(cornMask).clip(geometry).select('LST');
    var lstGrass = img.updateMask(grassMask).clip(geometry).select('LST').round();

    var cdfDict = buildGrasslandCdfDict(lstGrass, geometry);
    var L = likelihoodFromCdfDict(lstCorn, cdfDict).rename('L_' + id);

    likelihoodStack = likelihoodStack.addBands(L);
  }

  // (E) Combine likelihoods across scenes via log-product
  var combinedLogL = likelihoodStack.log().reduce(ee.Reducer.sum());
  var combinedL = combinedLogL.exp();
  var logCombinedL = combinedL.log();

  var oneMinus = likelihoodStack.multiply(-1).add(1);
  var combinedLogNotL = oneMinus.log().reduce(ee.Reducer.sum());
  var combinedNotL = combinedLogNotL.exp();
  var logCombinedNotL = combinedNotL.log();

  // (F) Prior median irrigation fraction (0–1)
  // If you are in custom-region mode, you may want to ignore stateUpper
  // and use regionNameUpper/yearInt only (modify getRegionYearIrrFraction accordingly).
  var priorMedian = getRegionYearIrrFraction(stateUpper, regionNameUpper, yearInt);

  // Beta prior parameters from desired median + concentration S
  var ab = betaParamsFromMedian(priorMedian, PRIOR_STRENGTH_S);
  var alpha = ee.Number(ab.get('alpha'));
  var beta  = ee.Number(ab.get('beta'));

  // (G) Posterior over p-grid
  var epsilon = 1e-6;
  var L_adj = combinedL.clamp(epsilon, 1 - epsilon);
  var notL_adj = combinedNotL.clamp(epsilon, 1 - epsilon);

  var logPostList = P_VALUES.map(function(p) {
    p = ee.Number(p);
    var oneMinusP = ee.Number(1).subtract(p);

    var mix = L_adj.multiply(p).add(notL_adj.multiply(oneMinusP));
    var pixelLogLike = mix.log();

    var logJointLike = pixelLogLike.reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: geometry,
      scale: SCALE_M,
      maxPixels: MAX_PIX
    }).values().get(0);

    var prior = betaPdfUnnorm(p, alpha, beta).add(epsilon);
    var logPrior = prior.log();

    return ee.Dictionary({p: p, log_posterior: ee.Number(logJointLike).add(logPrior)});
  });

  var logVals = ee.List(logPostList.map(function(d){ return ee.Dictionary(d).get('log_posterior'); }));
  var maxLog = ee.Number(logVals.reduce(ee.Reducer.max()));

  var postUnnorm = logPostList.map(function(d) {
    d = ee.Dictionary(d);
    return ee.Dictionary({
      p: d.get('p'),
      posterior: ee.Number(d.get('log_posterior')).subtract(maxLog).exp()
    });
  });

  var postSum = ee.Number(ee.List(postUnnorm).iterate(function(d, acc) {
    return ee.Number(acc).add(ee.Dictionary(d).getNumber('posterior'));
  }, ee.Number(0)));

  var postNorm = ee.List(postUnnorm).map(function(d) {
    d = ee.Dictionary(d);
    return d.set('posterior', d.getNumber('posterior').divide(postSum));
  });

  // (H) Marginalize p to get per-pixel irrigation probability
  var weightedBands = postNorm.map(function(d) {
    d = ee.Dictionary(d);
    var p = ee.Number(d.get('p'));
    var w = ee.Number(d.get('posterior'));

    var numer = combinedL.multiply(p);
    var denom = combinedL.multiply(p).add(combinedNotL.multiply(ee.Number(1).subtract(p)));

    return numer.divide(denom).multiply(w);
  });

  var posteriorMean = ee.ImageCollection(weightedBands)
    .toBands()
    .reduce(ee.Reducer.sum())
    .rename('posterior_mean');

  // (I) Diagnostics + export image
  var exportImage = posteriorMean
    .addBands(combinedL.rename('likelihood'))
    .addBands(logCombinedL.rename('log_likelihood'))
    .addBands(combinedNotL.rename('likelihood_rain'))
    .addBands(logCombinedNotL.rename('log_likelihood_rain'));

  // (J) EXPORT (YOU MUST CUSTOMIZE NAMING)
  // Replace these with your preferred naming scheme.
  //
  // Example description:
  //   'posterior_' + regionNameUpper + '_' + yearStr
  //
  // Example asset collection:
  //   OUTPUT_ASSET_COLLECTION = 'projects/ee-gfb46/assets/annual_maps'
  //
  // Example assetId:
  //   OUTPUT_ASSET_COLLECTION + '/posterior_' + regionNameUpper + '_' + yearStr
  //
  // IMPORTANT: OUTPUT_ASSET_COLLECTION must already exist.
  var description = 'INSERT_EXPORT_DESCRIPTION_HERE';
  var assetId = OUTPUT_ASSET_COLLECTION + '/INSERT_EXPORT_ASSET_NAME_HERE';

  Export.image.toAsset({
    image: exportImage.clip(geometry).float(),
    description: description,
    assetId: assetId,
    region: geometry,
    scale: SCALE_M,
    maxPixels: MAX_PIX
  });

  // Optional binary masks (not exported here)
  var irrigatedMask = posteriorMean.gte(POSTERIOR_THRESHOLD).selfMask();
  var rainMask = posteriorMean.lt(POSTERIOR_THRESHOLD).selfMask();
}
