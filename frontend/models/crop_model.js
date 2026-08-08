/**
 * Crop Model
 * Normalizes raw crop JSON data.
 */
export class Crop {
    constructor(data) {
        this.id = data.id;
        this.name = data.name;
        this.family = data.family;
        this.category = data.category;
        this.description = data.description;
        this.seasons = data.seasons || [];

        this.waterNeeds = {
            min: data.water_need_mm_min || 0,
            max: data.water_need_mm_max || 0,
            mid: ((data.water_need_mm_min || 0) + (data.water_need_mm_max || 0)) / 2
        };

        this.stressThresholds = {
            heat: data.heat_stress || 35,
            cold: data.cold_stress || 15
        };

        this.duration = {
            min: data.growth_duration_days_min || 90,
            max: data.growth_duration_days_max || 120
        };

        this.rotation = {
            goodPredecessors: data.good_predecessor_families || [],
            badPredecessors: data.bad_predecessor_families || []
        };

        this.economics = {
            marketVolatility: data.market_volatility || 'medium',
            yieldPotential: data.yield_potential || 7,
            marketPrice: data.market_price || 7,
            inputCost: data.input_cost || 6,
            mspCovered: data.msp_covered || false,
            mspPricePerQtl: data.msp_price_per_qtl || null,
            mspYear: data.msp_year || null
        };
    }
}
