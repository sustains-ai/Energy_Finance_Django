/**
 * Visualization module for climate data visualization
 */

// Global variables
let datasetId = null;
let datasetMetadata = null;
let currentData = null;
let currentVariable = null;
let currentVisualization = null;
let mapObject = null;
let chartObject = null;

/**
 * Initialize the visualization interface
 * @param {number} id - Dataset ID
 */
function initVisualization(id) {
    datasetId = id;
    
    // Load dataset metadata
    loadDatasetMetadata();
    
    // Set up event listeners
    document.getElementById('variable-select').addEventListener('change', onVariableChange);
    document.getElementById('viz-type').addEventListener('change', onVisualizationTypeChange);
    document.getElementById('update-viz').addEventListener('click', updateVisualization);
    document.getElementById('export-data').addEventListener('click', showExportModal);
    document.getElementById('download-image').addEventListener('click', downloadVisualization);
    document.getElementById('fullscreen-viz').addEventListener('click', toggleFullscreen);
    document.getElementById('do-export').addEventListener('click', exportData);
}

/**
 * Load dataset metadata from the API
 */
function loadDatasetMetadata() {
    // Show loading spinner
    document.getElementById('loading-metadata').style.display = 'block';
    document.getElementById('metadata-error').style.display = 'none';
    document.getElementById('control-panel').style.display = 'none';
    
    // Fetch metadata from the API
    fetch(`/api/dataset/${datasetId}/metadata`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                datasetMetadata = data.metadata;
                populateVariableSelect(datasetMetadata);
                document.getElementById('loading-metadata').style.display = 'none';
                document.getElementById('control-panel').style.display = 'block';
            } else {
                throw new Error(data.error || 'Failed to load metadata');
            }
        })
        .catch(error => {
            console.error('Error loading metadata:', error);
            document.getElementById('loading-metadata').style.display = 'none';
            document.getElementById('metadata-error').style.display = 'block';
            document.getElementById('metadata-error-message').textContent = error.message;
        });
}

/**
 * Populate the variable select dropdown with variables from the metadata
 * @param {Object} metadata - Dataset metadata
 */
function populateVariableSelect(metadata) {
    const variableSelect = document.getElementById('variable-select');
    
    // Clear existing options
    while (variableSelect.options.length > 1) {
        variableSelect.remove(1);
    }
    
    // Add variables from metadata
    if (metadata.variables) {
        for (const variable in metadata.variables) {
            // Skip dimension variables (usually lat, lon, time)
            if (variable in metadata.dimensions) continue;
            
            const option = document.createElement('option');
            option.value = variable;
            option.textContent = variable;
            variableSelect.appendChild(option);
        }
    }
}

/**
 * Handle variable selection change
 */
function onVariableChange() {
    const variableSelect = document.getElementById('variable-select');
    const selectedVariable = variableSelect.value;
    
    if (selectedVariable && datasetMetadata.variables[selectedVariable]) {
        currentVariable = selectedVariable;
        
        // Show variable info
        const varInfo = document.getElementById('variable-info');
        const varName = document.getElementById('variable-name');
        const varDesc = document.getElementById('variable-description');
        const varUnits = document.getElementById('variable-units');
        
        varInfo.style.display = 'block';
        varName.textContent = selectedVariable;
        
        // Get variable attributes
        const attributes = datasetMetadata.variables[selectedVariable].attributes || {};
        
        // Set description and units
        let description = attributes.long_name || attributes.standard_name || 'No description';
        let units = attributes.units || 'No units';
        
        varDesc.textContent = description;
        varUnits.textContent = `Units: ${units}`;
    } else {
        document.getElementById('variable-info').style.display = 'none';
    }
}

/**
 * Handle visualization type change
 */
function onVisualizationTypeChange() {
    const vizType = document.getElementById('viz-type').value;
    const timeControls = document.getElementById('time-controls');
    const geoControls = document.getElementById('geographic-controls');
    
    // Show/hide appropriate controls based on visualization type
    if (vizType === 'timeseries') {
        timeControls.style.display = 'none';  // Time series shows all time steps
        geoControls.style.display = 'block';
    } else if (vizType === 'map' || vizType === 'heatmap') {
        timeControls.style.display = 'block';
        geoControls.style.display = 'block';
    } else if (vizType === 'histogram') {
        timeControls.style.display = 'block';
        geoControls.style.display = 'block';
    }
}

/**
 * Update the visualization with current settings
 */
function updateVisualization() {
    // Get selected options
    const variable = document.getElementById('variable-select').value;
    const vizType = document.getElementById('viz-type').value;
    const latMin = document.getElementById('lat-min').value;
    const latMax = document.getElementById('lat-max').value;
    const lonMin = document.getElementById('lon-min').value;
    const lonMax = document.getElementById('lon-max').value;
    
    // Validate inputs
    if (!variable) {
        alert('Please select a variable to visualize');
        return;
    }
    
    // Build query parameters
    const params = new URLSearchParams({
        variable: variable,
        lat_range: `${latMin}:${latMax}`,
        lon_range: `${lonMin}:${lonMax}`
    });
    
    // Add time parameter if time control is visible and has a selection
    const timeSelect = document.getElementById('time-select');
    if (timeSelect.style.display !== 'none' && timeSelect.value !== '') {
        params.append('time_range', timeSelect.value);
    }
    
    // Show loading spinner
    document.getElementById('loading-viz').style.display = 'block';
    document.getElementById('viz-error').style.display = 'none';
    document.getElementById('no-data-selected').style.display = 'none';
    document.getElementById('map-container').style.display = 'none';
    document.getElementById('chart-container').style.display = 'none';
    
    // Fetch data from the API
    fetch(`/api/dataset/${datasetId}/data?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentData = data.data;
                currentVariable = variable;
                
                // Update statistics
                updateStatistics(data.data.statistics);
                
                // Create visualization based on type
                createVisualization(vizType, data.data);
                
                document.getElementById('loading-viz').style.display = 'none';
                document.getElementById('viz-stats').style.display = 'block';
            } else {
                throw new Error(data.error || 'Failed to load data');
            }
        })
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('loading-viz').style.display = 'none';
            document.getElementById('viz-error').style.display = 'block';
            document.getElementById('viz-error-message').textContent = error.message;
        });
}

/**
 * Create visualization based on the selected type
 * @param {string} type - Visualization type
 * @param {Object} data - Data to visualize
 */
function createVisualization(type, data) {
    currentVisualization = type;
    
    // Clear previous visualization
    if (mapObject) {
        mapObject.remove();
        mapObject = null;
    }
    
    if (chartObject) {
        Plotly.purge('chart-container');
        chartObject = null;
    }
    
    // Create new visualization
    if (type === 'map') {
        document.getElementById('map-container').style.display = 'block';
        document.getElementById('chart-container').style.display = 'none';
        createMap(data);
    } else if (type === 'timeseries') {
        document.getElementById('map-container').style.display = 'none';
        document.getElementById('chart-container').style.display = 'block';
        createTimeSeries(data);
    } else if (type === 'histogram') {
        document.getElementById('map-container').style.display = 'none';
        document.getElementById('chart-container').style.display = 'block';
        createHistogram(data);
    } else if (type === 'heatmap') {
        document.getElementById('map-container').style.display = 'none';
        document.getElementById('chart-container').style.display = 'block';
        createHeatmap(data);
    }
}

/**
 * Create a geographic map visualization
 * @param {Object} data - Data to visualize
 */
function createMap(data) {
    const mapContainer = document.getElementById('map-container');
    const colormap = document.getElementById('colormap').value;
    
    // Create map container
    mapContainer.innerHTML = '';
    
    // Check if we have sufficient data
    if (!data.data || !data.longitudes || !data.latitudes) {
        mapContainer.innerHTML = '<div class="alert alert-warning">Insufficient data for map visualization</div>';
        return;
    }
    
    // Create a Plotly map
    const plotData = [{
        type: 'contour',
        z: data.data,
        x: data.longitudes[0],  // Assuming all rows have the same longitude values
        y: data.latitudes.map(row => row[0]),  // Get first column of latitudes
        colorscale: colormap,
        contours: {
            coloring: 'heatmap',
            showlabels: true
        },
        colorbar: {
            title: `${data.variable} (${data.units})`
        }
    }];
    
    const layout = {
        title: `${data.variable} - Geographic Map`,
        xaxis: {
            title: 'Longitude'
        },
        yaxis: {
            title: 'Latitude'
        },
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50
        }
    };
    
    Plotly.newPlot('map-container', plotData, layout, {responsive: true});
    mapObject = document.getElementById('map-container');
}

/**
 * Create a time series visualization
 * @param {Object} data - Data to visualize
 */
function createTimeSeries(data) {
    const chartContainer = document.getElementById('chart-container');
    const colormap = document.getElementById('colormap').value;
    
    // Create chart container
    chartContainer.innerHTML = '';
    
    // Check if we have sufficient data
    if (!data.data || !data.times) {
        chartContainer.innerHTML = '<div class="alert alert-warning">Insufficient data for time series visualization</div>';
        return;
    }
    
    // Process data for time series
    const timeValues = data.times;
    const dataValues = [];
    
    // Calculate area-weighted average for each time step
    for (let t = 0; t < timeValues.length; t++) {
        let sum = 0;
        let count = 0;
        
        for (let i = 0; i < data.data.length; i++) {
            for (let j = 0; j < data.data[i].length; j++) {
                if (!isNaN(data.data[i][j][t])) {
                    sum += data.data[i][j][t];
                    count++;
                }
            }
        }
        
        dataValues.push(count > 0 ? sum / count : null);
    }
    
    // Create a Plotly time series
    const plotData = [{
        type: 'scatter',
        mode: 'lines+markers',
        x: timeValues,
        y: dataValues,
        line: {
            color: getColorFromColormap(colormap, 0.5),
            width: 2
        },
        marker: {
            color: getColorFromColormap(colormap, 0.5),
            size: 6
        }
    }];
    
    const layout = {
        title: `${data.variable} - Time Series`,
        xaxis: {
            title: 'Time'
        },
        yaxis: {
            title: `${data.variable} (${data.units})`
        },
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50
        }
    };
    
    Plotly.newPlot('chart-container', plotData, layout, {responsive: true});
    chartObject = document.getElementById('chart-container');
}

/**
 * Create a histogram visualization
 * @param {Object} data - Data to visualize
 */
function createHistogram(data) {
    const chartContainer = document.getElementById('chart-container');
    const colormap = document.getElementById('colormap').value;
    
    // Create chart container
    chartContainer.innerHTML = '';
    
    // Check if we have sufficient data
    if (!data.data) {
        chartContainer.innerHTML = '<div class="alert alert-warning">Insufficient data for histogram visualization</div>';
        return;
    }
    
    // Process data for histogram
    const values = [];
    
    // Flatten the data array
    for (let i = 0; i < data.data.length; i++) {
        for (let j = 0; j < data.data[i].length; j++) {
            // If data is 3D (with time dimension)
            if (Array.isArray(data.data[i][j])) {
                for (let t = 0; t < data.data[i][j].length; t++) {
                    if (!isNaN(data.data[i][j][t])) {
                        values.push(data.data[i][j][t]);
                    }
                }
            } else {
                // If data is 2D
                if (!isNaN(data.data[i][j])) {
                    values.push(data.data[i][j]);
                }
            }
        }
    }
    
    // Create a Plotly histogram
    const plotData = [{
        type: 'histogram',
        x: values,
        marker: {
            color: getColorFromColormap(colormap, 0.5)
        },
        opacity: 0.7,
        nbinsx: 30
    }];
    
    const layout = {
        title: `${data.variable} - Histogram`,
        xaxis: {
            title: `${data.variable} (${data.units})`
        },
        yaxis: {
            title: 'Frequency'
        },
        bargap: 0.05,
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50
        }
    };
    
    Plotly.newPlot('chart-container', plotData, layout, {responsive: true});
    chartObject = document.getElementById('chart-container');
}

/**
 * Create a heatmap visualization
 * @param {Object} data - Data to visualize
 */
function createHeatmap(data) {
    const chartContainer = document.getElementById('chart-container');
    const colormap = document.getElementById('colormap').value;
    
    // Create chart container
    chartContainer.innerHTML = '';
    
    // Check if we have sufficient data
    if (!data.data || !data.longitudes || !data.latitudes) {
        chartContainer.innerHTML = '<div class="alert alert-warning">Insufficient data for heatmap visualization</div>';
        return;
    }
    
    // Get a single time slice if data has time dimension
    let heatmapData;
    if (Array.isArray(data.data[0][0])) {
        // 3D data (with time) - take the first time step
        heatmapData = data.data.map(row => row.map(cell => cell[0]));
    } else {
        // 2D data
        heatmapData = data.data;
    }
    
    // Create a Plotly heatmap
    const plotData = [{
        type: 'heatmap',
        z: heatmapData,
        x: data.longitudes[0],  // Assuming all rows have the same longitude values
        y: data.latitudes.map(row => row[0]),  // Get first column of latitudes
        colorscale: colormap,
        colorbar: {
            title: `${data.variable} (${data.units})`
        }
    }];
    
    const layout = {
        title: `${data.variable} - Heatmap`,
        xaxis: {
            title: 'Longitude'
        },
        yaxis: {
            title: 'Latitude'
        },
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50
        }
    };
    
    Plotly.newPlot('chart-container', plotData, layout, {responsive: true});
    chartObject = document.getElementById('chart-container');
}

/**
 * Update statistics display
 * @param {Object} statistics - Statistics to display
 */
function updateStatistics(statistics) {
    document.getElementById('stat-min').textContent = statistics.min.toFixed(2);
    document.getElementById('stat-max').textContent = statistics.max.toFixed(2);
    document.getElementById('stat-mean').textContent = statistics.mean.toFixed(2);
    document.getElementById('stat-std').textContent = statistics.std.toFixed(2);
}

/**
 * Show the export modal
 */
function showExportModal() {
    if (!currentData) {
        alert('No data available to export');
        return;
    }
    
    const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
    exportModal.show();
}

/**
 * Export the current data
 */
function exportData() {
    if (!currentData) {
        alert('No data available to export');
        return;
    }
    
    const format = document.getElementById('export-format').value;
    const dataType = document.getElementById('export-data-type').value;
    
    // Create filename
    const filename = `${currentVariable}_${new Date().toISOString().slice(0, 10)}.${format}`;
    
    if (format === 'csv') {
        exportToCSV(filename, dataType);
    } else if (format === 'json') {
        exportToJSON(filename, dataType);
    }
    
    // Close the modal
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
}

/**
 * Export data to CSV format
 * @param {string} filename - Output filename
 * @param {string} dataType - Data type to export (current or full)
 */
function exportToCSV(filename, dataType) {
    let csv = 'latitude,longitude,value\n';
    
    // Process data based on format
    if (Array.isArray(currentData.data[0][0])) {
        // 3D data (with time)
        for (let i = 0; i < currentData.data.length; i++) {
            for (let j = 0; j < currentData.data[i].length; j++) {
                const lat = currentData.latitudes[i][j];
                const lon = currentData.longitudes[i][j];
                
                if (dataType === 'current') {
                    // Export only the first time step
                    const value = currentData.data[i][j][0];
                    if (!isNaN(value)) {
                        csv += `${lat},${lon},${value}\n`;
                    }
                } else {
                    // Export all time steps
                    for (let t = 0; t < currentData.data[i][j].length; t++) {
                        const value = currentData.data[i][j][t];
                        if (!isNaN(value)) {
                            csv += `${lat},${lon},${value}\n`;
                        }
                    }
                }
            }
        }
    } else {
        // 2D data
        for (let i = 0; i < currentData.data.length; i++) {
            for (let j = 0; j < currentData.data[i].length; j++) {
                const lat = currentData.latitudes[i][j];
                const lon = currentData.longitudes[i][j];
                const value = currentData.data[i][j];
                
                if (!isNaN(value)) {
                    csv += `${lat},${lon},${value}\n`;
                }
            }
        }
    }
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Export data to JSON format
 * @param {string} filename - Output filename
 * @param {string} dataType - Data type to export (current or full)
 */
function exportToJSON(filename, dataType) {
    let exportData;
    
    if (dataType === 'current') {
        // Export only the current visualization
        exportData = {
            variable: currentData.variable,
            units: currentData.units,
            data: currentData.data,
            latitudes: currentData.latitudes,
            longitudes: currentData.longitudes
        };
        
        // Add times if available
        if (currentData.times) {
            exportData.times = currentData.times;
        }
    } else {
        // Export full dataset (same as current since we only have what was loaded)
        exportData = currentData;
    }
    
    // Create download link
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Download the current visualization as an image
 */
function downloadVisualization() {
    if (!currentVisualization) {
        alert('No visualization to download');
        return;
    }
    
    const filename = `${currentVariable}_${currentVisualization}_${new Date().toISOString().slice(0, 10)}.png`;
    
    if (currentVisualization === 'map') {
        Plotly.downloadImage('map-container', {
            format: 'png',
            filename: filename,
            width: 1200,
            height: 800
        });
    } else {
        Plotly.downloadImage('chart-container', {
            format: 'png',
            filename: filename,
            width: 1200,
            height: 800
        });
    }
}

/**
 * Toggle fullscreen mode for the visualization
 */
function toggleFullscreen() {
    const container = currentVisualization === 'map' ? 
        document.getElementById('map-container') : 
        document.getElementById('chart-container');
    
    if (!document.fullscreenElement) {
        container.requestFullscreen().catch(err => {
            alert(`Error attempting to enable fullscreen mode: ${err.message}`);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

/**
 * Get a color from a colormap
 * @param {string} colormap - Colormap name
 * @param {number} value - Value between 0 and 1
 * @returns {string} - Color in RGB format
 */
function getColorFromColormap(colormap, value) {
    // Simple function to get a color from a named colormap
    const colormaps = {
        viridis: ['#440154', '#433982', '#30678D', '#218F8B', '#36B677', '#8ED542', '#FDE725'],
        plasma: ['#0D0887', '#5B02A3', '#9A179B', '#CB4678', '#EB7852', '#FBB32F', '#F0F921'],
        inferno: ['#000004', '#320A5A', '#781C6D', '#BB3654', '#EC6824', '#FBB41A', '#FCFFA4'],
        magma: ['#000004', '#2C105C', '#711F81', '#B63679', '#EE605E', '#FDAE78', '#FCFDBF'],
        cividis: ['#00224E', '#123570', '#3B496C', '#575E6A', '#707173', '#8A8678', '#A59C74', '#C2B26B', '#E0CA60'],
        RdBu: ['#67001F', '#B2182B', '#D6604D', '#F4A582', '#FDDBC7', '#D1E5F0', '#92C5DE', '#4393C3', '#2166AC', '#053061'],
        BrBG: ['#543005', '#8C510A', '#BF812D', '#DFC27D', '#F6E8C3', '#C7EAE5', '#80CDC1', '#35978F', '#01665E', '#003C30'],
        YlOrRd: ['#FFFFCC', '#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'],
        YlGnBu: ['#FFFFD9', '#EDF8B1', '#C7E9B4', '#7FCDBB', '#41B6C4', '#1D91C0', '#225EA8', '#253494', '#081D58']
    };
    
    // Default to viridis if colormap not found
    const colors = colormaps[colormap] || colormaps.viridis;
    
    // Clamp value between 0 and 1
    const clampedValue = Math.max(0, Math.min(value, 1));
    
    // Get index in color array
    const index = Math.floor(clampedValue * (colors.length - 1));
    
    return colors[index];
}
