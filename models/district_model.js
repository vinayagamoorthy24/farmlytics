/**
 * District Model (v7.4 - Scientific Edition)
 * Normalizes raw district JSON data into a consistent object.
 */
export class District {
    static SCHEMA_VERSION = 'v7.4';

    constructor(data) {
        this.schemaVersion = data.schemaVersion || District.SCHEMA_VERSION;
        this.id = data.id;
        this.name = data.district;
        this.state = data.state;
        this.zone = data.agro_climatic_zone;
        this.annualRainfall = data.avg_annual_rainfall_mm;
        this.rainfallShares = data.seasonal_rainfall_share || {};
        this.tempAvg = data.seasonal_temp_avg || {};
        this.tempVariability = data.temp_variability_index || 'medium';
        this.rainfallCV = data.rainfall_cv_percent || 25;
        this.soil = {
            type: data.soil_type,
            drainage: data.soil_drainage,
            texture: data.soil_texture || 'loam'
        };
        this.source = data.source;
        this.dataQuality = data.data_quality_index || 1.0;
    }

    /**
     * Scientific Confidence Model (Geometric Mean)
     * Prevents aggressive collapse while maintaining compounding uncertainty.
     */
    getConfidenceScore() {
        // 1. Data Completeness Factor (0.0 - 1.0)
        const completeness = this.dataQuality;

        // 2. Climate Stability Factor (0.0 - 1.0)
        let stabilityFactor = 1.0;
        if (this.rainfallCV >= 40) stabilityFactor = 0.6;
        else if (this.rainfallCV >= 30) stabilityFactor = 0.8;
        else if (this.rainfallCV >= 20) stabilityFactor = 0.95;

        // 3. Model Assumption Factor (Structural uncertainty)
        const modelFactor = 0.85;

        // Geometric Mean: (a * b * c)^(1/3)
        const totalConfidence = Math.pow(completeness * stabilityFactor * modelFactor, 1 / 3);

        if (totalConfidence >= 0.85) return "High";
        if (totalConfidence >= 0.70) return "Moderate";
        return "Low";
    }

    /**
     * Calculates Effective Rainfall based on FAO Efficiency Factors
     * Accounting for runoff and deep percolation losses by soil texture.
     */
    getEffectiveSeasonalRainfall(season) {
        const rawRain = this.getSeasonalRainfall(season);

        // FAO Efficiency Coefficients by Soil Texture
        const efficiency = {
            'sand': 0.50,
            'loam': 0.65,
            'clay': 0.75
        };

        const texture = (this.soil.texture || 'loam').toLowerCase();
        const factor = efficiency[texture] || 0.65;

        return Math.round(rawRain * factor);
    }

    getSeasonalRainfall(season) {
        const share = this.rainfallShares[season.toLowerCase()] || 0;
        return Math.round(this.annualRainfall * share);
    }

    getSeasonalTemp(season) {
        return this.tempAvg[season.toLowerCase()] || 28;
    }

    static fromJSON(data) {
        return new District(data);
    }
}
