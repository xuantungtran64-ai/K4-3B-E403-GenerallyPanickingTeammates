(function () {
    const STORAGE_KEY = 'qa-radar-api-config';
    const defaults = { baseUrl: '', statsPath: '', clustersPath: '', actionPath: '', historyPath: '' };

    function getConfig() {
        try {
            return { ...defaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') };
        } catch (error) {
            return { ...defaults };
        }
    }

    function saveConfig(config) {
        const cleaned = Object.fromEntries(Object.entries({ ...defaults, ...config }).map(([key, value]) => [key, String(value || '').trim()]));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned));
        return cleaned;
    }

    function resolveUrl(path) {
        const config = getConfig();
        if (!config.baseUrl || !path) throw new Error('Chưa cấu hình endpoint API.');
        return new URL(path, config.baseUrl.endsWith('/') ? config.baseUrl : `${config.baseUrl}/`).toString();
    }

    async function request(path, options = {}) {
        let response;
        try {
            response = await fetch(resolveUrl(path), { ...options, headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...(options.headers || {}) } });
        } catch (error) {
            throw new Error('Không thể kết nối backend. Kiểm tra server và CORS.');
        }
        const contentType = response.headers.get('content-type') || '';
        const body = contentType.includes('application/json') ? await response.json() : await response.text();
        if (!response.ok) throw new Error(body?.message || body?.detail || `Backend trả về lỗi HTTP ${response.status}.`);
        return body;
    }

    function pathFor(key) {
        const path = getConfig()[key];
        if (!path) throw new Error(`Chưa cấu hình route ${key}.`);
        return path;
    }

    window.QARadarApi = {
        getConfig,
        saveConfig,
        request,
        isConfigured: () => Boolean(getConfig().baseUrl && getConfig().clustersPath),
        getStats: () => {
            const path = getConfig().statsPath;
            return path ? request(path) : Promise.resolve(null);
        },
        getClusters: () => request(pathFor('clustersPath')),
        getHistory: () => {
            const path = getConfig().historyPath;
            return path ? request(path) : Promise.resolve([]);
        },
        updateCluster: (id, payload) => request(pathFor('actionPath').replace('{id}', encodeURIComponent(id)), { method: 'PATCH', body: JSON.stringify(payload) })
    };
}());
