import { District } from '../models/district_model.js?v=8.0';
import { Crop } from '../models/crop_model.js?v=8.0';

/**
 * Dataset Loader Service
 * Handles loading, versioning, and normalization of agricultural datasets.
 */
export async function loadDatasets(version = 'v8.0') {
    const urls = {
        crops: `/data/crops.json?${version}`,
        districts: `/data/districts.json?${version}`,
        climate: `/data/climate_constants.json?${version}`,
        soil: `/data/soil_rules.json?${version}`
    };

    try {
        const [resCrops, resDist, resClimate, resSoil] = await Promise.all([
            fetch(urls.crops),
            fetch(urls.districts),
            fetch(urls.climate),
            fetch(urls.soil)
        ]);

        const rawData = {
            crops: await resCrops.json(),
            districts: await resDist.json(),
            climate: await resClimate.json(),
            soil: await resSoil.json()
        };

        // Normalize Data using Models
        const districts = rawData.districts.map(d => new District(d));
        const crops = rawData.crops.map(c => new Crop(c));

        const datasets = {
            crops,
            districts,
            climate: rawData.climate,
            soil: rawData.soil
        };

        // Build Lookups
        datasets.cropLookup = {};
        datasets.crops.forEach(c => datasets.cropLookup[c.id] = c);

        datasets.districtLookup = {};
        datasets.districts.forEach(d => datasets.districtLookup[d.id] = d);

        return datasets;
    } catch (err) {
        console.error("Dataset loader failed:", err);
        throw err;
    }
}
