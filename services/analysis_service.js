/**
 * Analysis Service — Lightweight API Client (v9.0)
 * Delegates all calculation & explanation logic to the Python backend (/api/analyze).
 */
export async function runAnalysis(input) {
    const payload = {
        district: input.districtId,
        season: input.season,
        irrigation: input.irrigation,
        previous_crop: input.prevCropId || null,
        has_residue: Boolean(input.hasResidue),
        has_fertilizer: Boolean(input.hasFertilizer)
    };

    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'API Request Failed' }));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    return await response.json();
}
