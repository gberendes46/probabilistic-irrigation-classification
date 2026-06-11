/**** 
 * 02_mosaic_and_export_tif
 *
 * Mosaics per-county posterior assets from 01_make_annual_maps into one
 * statewide image per year and exports each as a GeoTIFF to Google Drive.
 *
 * Run after all 01_make_annual_maps export tasks have completed (all blue
 * in the Tasks tab).
 *
 * The exported GeoTIFFs are the files archived on HydroShare.
 ****/

/* =============================================================================
 * USER SETTINGS (EDIT THESE)
 * =============================================================================
 */

// Asset collection produced by 01_make_annual_maps
// Each asset inside should be named: COUNTY_YEAR (e.g. ADAMS_2009)
var ASSET_COLLECTION = 'INSERT_YOUR_ASSET_COLLECTION_PATH_HERE';
// Example: 'projects/ee-gfb46/assets/annual_maps'

// Years to mosaic and export
var YEARS = [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
             2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018,
             2019, 2020, 2021, 2022, 2023];

// Band to export ('posterior_mean' is the primary product)
var BAND = 'posterior_mean';

// Google Drive folder to export into
var DRIVE_FOLDER = 'GEE_exports';

// Bounding box of your study area
// Default below is Nebraska
var EXPORT_REGION = ee.Geometry.Rectangle([-104.06, 39.99, -95.31, 43.00]);

// Export scale in meters (30 = native Landsat resolution)
var SCALE_M = 30;

// String prefix shared by all per-county asset names for a given year.
// If your assets are named 'posterior_ADAMS_2009', the year string '2009'
// appears at the end. The filter below matches on that.
// If your naming convention differs, adjust the filter in the loop below.
var ASSET_NAME_SUFFIX = true; // true = year appears at end of asset name

/* =============================================================================
 * MOSAIC AND EXPORT
 * =============================================================================
 */

var collection = ee.ImageCollection(ASSET_COLLECTION);

YEARS.forEach(function(year) {
  var yearStr = String(year);

  // Filter to all county assets for this year
  var yearCollection = collection.filter(
    ee.Filter.stringEndsWith('system:index', yearStr)
  );

  // Mosaic (first valid pixel wins where counties overlap at borders)
  var mosaic = yearCollection
    .select(BAND)
    .mosaic()
    .rename('p_irrigated')
    .clip(EXPORT_REGION);

  Export.image.toDrive({
    image: mosaic.float(),
    description: 'NE_posterior_' + yearStr,
    folder: DRIVE_FOLDER,
    fileNamePrefix: 'NE_posterior_' + yearStr,
    region: EXPORT_REGION,
    scale: SCALE_M,
    crs: 'EPSG:4326',
    fileFormat: 'GeoTIFF',
    maxPixels: 1e13
  });

  print('Queued: NE_posterior_' + yearStr);
});

print('All tasks queued — go to the Tasks tab and click Run on each one.');
