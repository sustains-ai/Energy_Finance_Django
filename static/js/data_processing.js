/**
 * Data processing module for climate analysis
 */

// Global variables
let datasetId = null;
let datasetMetadata = null;
let currentAnalysis = null;
let currentAnalysisId = null;
let analysisTypes = [];

/**
 * Initialize the analysis interface
 * @param {number} id - Dataset ID
 * @param {Array} types - Available analysis types
 */
function initAnalysis(id, types) {
    datasetId = id;
    analysisTypes = types;
    
    // Load dataset metadata
    loadDatasetMetadata();
    
    // Set up event listeners
    document.getElementById('analysis-type').addEventListener('change', onAnalysisTypeChange);
    document.getElementById('variable-select').addEventListener('change', onVariableChange);
    document.getElementById('run-analysis').addEventListener('click', runAnalysis);
    document.getElementById('download-result').addEventListener('click', downloadResult);
    document.getElementById('export-result').addEventListener('click', showExportModal);
    document.getElementById('do-export').addEventListener('click', exportResult);
}

/**
 * Load dataset metadata from the API
 */
function loadDatasetMetadata() {
    // Show loading spinner
    document.getElementById('loading-metadata').style.display = 'block';
    document.getElementById('metadata-error').style.display = 'none';
    
    // Fetch metadata from the API
    fetch(`/api/dataset/${datasetId}/metadata`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                datasetMetadata = data.metadata;
                populateVariableSelect(datasetMetadata);
                document.getElementById('loading-metadata').style.display = 'none';
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
 * Handle analysis type selection change
 */
function onAnalysisTypeChange() {
    const analysisTypeSelect = document.getElementById('analysis-type');
    const selectedType = analysisTypeSelect.value;
    
    // Show/hide appropriate parameter sections
    document.getElementById('temp-anomaly-params').style.display = 
        (selectedType === 'temperature_anomaly') ? 'block' : 'none';
    document.getElementById('climate-indices-params').style.display = 
        (selectedType === 'climate_indices') ? 'block' : 'none';
    
    // Update description
    const descriptionDiv = document.getElementById('analysis-description');
    const analysisNameHeader = document.getElementById('analysis-name');
    const analysisDescText = document.getElementById('analysis-desc-text');
    
    if (selectedType) {
        // Find the selected analysis type in the provided types array
        const selectedAnalysis = analysisTypes.find(type => type.id === selectedType);
        
        if (selectedAnalysis) {
            analysisNameHeader.textContent = selectedAnalysis.name;
            analysisDescText.textContent = selectedAnalysis.description;
            descriptionDiv.style.display = 'block';
        } else {
            descriptionDiv.style.display = 'none';
        }
    } else {
        descriptionDiv.style.display = 'none';
    }
}

/**
 * Handle variable selection change
 */
function onVariableChange() {
    // This could be used to update UI based on variable selection
    // For example, showing variable-specific parameters
}

/**
 * Run climate analysis with current settings
 */
function runAnalysis() {
    // Get form values
    const analysisType = document.getElementById('analysis-type').value;
    const variable = document.getElementById('variable-select').value;
    
    // Validate inputs
    if (!analysisType) {
        alert('Please select an analysis type');
        return;
    }
    
    if (!variable) {
        alert('Please select a variable to analyze');
        return;
    }
    
    // Prepare analysis parameters
    const parameters = {
        variable: variable
    };
    
    // Add analysis-specific parameters
    if (analysisType === 'temperature_anomaly') {
        parameters.baseline_start = document.getElementById('baseline-start').value;
        parameters.baseline_end = document.getElementById('baseline-end').value;
    } else if (analysisType === 'climate_indices') {
        parameters.index_type = document.getElementById('index-type').value;
    }
    
    // Show loading spinner
    document.getElementById('loading-analysis').style.display = 'block';
    document.getElementById('analysis-error').style.display = 'none';
    document.getElementById('no-analysis-selected').style.display = 'none';
    document.getElementById('analysis-container').style.display = 'none';
    
    // Run analysis through API
    fetch(`/api/dataset/${datasetId}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            analysis_type: analysisType,
            parameters: parameters
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Save the analysis ID for loading results
            currentAnalysisId = data.analysis_id;
            
            // Load the analysis results
            loadAnalysisResult(currentAnalysisId);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('Error in analysis:', error);
        document.getElementById('loading-analysis').style.display = 'none';
        document.getElementById('analysis-error').style.display = 'block';
        document.getElementById('analysis-error-message').textContent = error.message;
    });
}

/**
 * Load analysis result
 * @param {number} analysisId - Analysis ID to load
 */
function loadAnalysisResult(analysisId) {
    // Show loading spinner
    document.getElementById('loading-analysis').style.display = 'block';
    document.getElementById('analysis-error').style.display = 'none';
    
    // Load analysis results
    fetch(`/api/analysis/${analysisId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentAnalysis = data.result;
                
                // Display the analysis results
                displayAnalysisResult(currentAnalysis);
                
                // Enable download and export buttons
                document.getElementById('download-result').disabled = false;
                document.getElementById('export-result').disabled = false;
                
                // Update statistics
                updateAnalysisStats(currentAnalysis);
                
                document.getElementById('loading-analysis').style.display = 'none';
                document.getElementById('analysis-container').style.display = 'block';
                document.getElementById('analysis-stats').style.display = 'block';
            } else {
                throw new Error(data.error || 'Failed to load analysis results');
            }
        })
        .catch(error => {
            console.error('Error loading analysis results:', error);
            document.getElementById('loading-analysis').style.display = 'none';
            document.getElementById('analysis-error').style.display = 'block';
            document.getElementById('analysis-error-message').textContent = error.message;
        });
}

/**
 * Load a past analysis result
 * @param {number} analysisId - Analysis ID to load
 */
function loadPastAnalysis(analysisId) {
    // Save the current analysis ID
    currentAnalysisId = analysisId;
    
    // Load the analysis result
    loadAnalysisResult(analysisId);
    
    // Scroll to the result container
    document.getElementById('analysis-container').scrollIntoView({
        behavior: 'smooth'
    });
}

/**
 * Display analysis result
 * @param {Object} result - Analysis result to display
 */
function displayAnalysisResult(result) {
    const container = document.getElementById('analysis-result-visualization');
    const textResult = document.getElementById('analysis-text-result');
    
    // Clear previous results
    container.innerHTML = '';
    textResult.innerHTML = '';
    
    // Get analysis type and result
    const analysisType = result.analysis_type;
    const analysisResult = result.result;
    
    // Check for error in the analysis
    if (result.error) {
        textResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error in analysis: ${result.error}
            </div>
        `;
        return;
    }
    
    // Display results based on analysis type
    if (analysisType === 'temperature_mean') {
        displayTemperatureMean(container, textResult, analysisResult);
    } else if (analysisType === 'temperature_anomaly') {
        displayTemperatureAnomaly(container, textResult, analysisResult);
    } else if (analysisType === 'precipitation_total') {
        displayPrecipitationTotal(container, textResult, analysisResult);
    } else if (analysisType === 'climate_indices') {
        displayClimateIndices(container, textResult, analysisResult);
    } else if (analysisType === 'seasonal_cycle') {
        displaySeasonalCycle(container, textResult, analysisResult);
    } else {
        textResult.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-circle me-2"></i>
                Unsupported analysis type: ${analysisType}
            </div>
        `;
    }
}

/**
 * Display temperature mean analysis result
 * @param {HTMLElement} container - Result visualization container
 * @param {HTMLElement} textResult - Text result container
 * @param {Object} result - Analysis result data
 */
function displayTemperatureMean(container, textResult, result) {
    // Create a map visualization
    const data = [{
        type: 'contour',
        z: result.mean_temperature,
        x: result.longitudes[0],  // Assuming all rows have the same longitude values
        y: result.latitudes.map(row => row[0]),  // Get first column of latitudes
        colorscale: 'RdBu',
        reversescale: true,
        contours: {
            coloring: 'heatmap',
            showlabels: true
        },
        colorbar: {
            title: `Temperature (${result.units})`
        }
    }];
    
    const layout = {
        title: 'Mean Temperature',
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
    
    Plotly.newPlot(container, data, layout, {responsive: true});
    
    // Add text summary
    const temperatures = result.mean_temperature.flat();
    const validTemps = temperatures.filter(t => !isNaN(t));
    const min = Math.min(...validTemps).toFixed(2);
    const max = Math.max(...validTemps).toFixed(2);
    const mean = (validTemps.reduce((a, b) => a + b, 0) / validTemps.length).toFixed(2);
    
    textResult.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-thermometer-half me-2"></i>Temperature Summary</h5>
            </div>
            <div class="card-body">
                <p>The mean temperature analysis shows the average temperature across the spatial domain.</p>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Minimum</h6>
                                <p class="card-text display-6">${min}°</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Mean</h6>
                                <p class="card-text display-6">${mean}°</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Maximum</h6>
                                <p class="card-text display-6">${max}°</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Display temperature anomaly analysis result
 * @param {HTMLElement} container - Result visualization container
 * @param {HTMLElement} textResult - Text result container
 * @param {Object} result - Analysis result data
 */
function displayTemperatureAnomaly(container, textResult, result) {
    // Create a container for the time slider
    const sliderContainer = document.createElement('div');
    sliderContainer.id = 'time-slider-container';
    sliderContainer.className = 'mb-3';
    
    const sliderLabel = document.createElement('label');
    sliderLabel.className = 'form-label';
    sliderLabel.textContent = 'Time Step:';
    sliderContainer.appendChild(sliderLabel);
    
    const sliderRow = document.createElement('div');
    sliderRow.className = 'row align-items-center';
    
    const sliderCol = document.createElement('div');
    sliderCol.className = 'col-10';
    
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.className = 'form-range';
    slider.id = 'time-slider';
    slider.min = 0;
    slider.max = result.times.length - 1;
    slider.value = 0;
    sliderCol.appendChild(slider);
    
    const valueCol = document.createElement('div');
    valueCol.className = 'col-2';
    
    const sliderValue = document.createElement('span');
    sliderValue.id = 'time-slider-value';
    sliderValue.textContent = result.times[0];
    valueCol.appendChild(sliderValue);
    
    sliderRow.appendChild(sliderCol);
    sliderRow.appendChild(valueCol);
    sliderContainer.appendChild(sliderRow);
    
    // Insert slider before the plot container
    container.parentNode.insertBefore(sliderContainer, container);
    
    // Create a map visualization for anomaly
    const createAnomalyPlot = (timeIndex) => {
        // Extract the data for the selected time step
        const anomalyData = result.anomaly.map(row => 
            row.map(cell => cell[timeIndex])
        );
        
        const data = [{
            type: 'contour',
            z: anomalyData,
            x: result.longitudes[0],  // Assuming all rows have the same longitude values
            y: result.latitudes.map(row => row[0]),  // Get first column of latitudes
            colorscale: 'RdBu',
            reversescale: true,
            contours: {
                coloring: 'heatmap',
                showlabels: true
            },
            colorbar: {
                title: `Temperature Anomaly (${result.units})`
            }
        }];
        
        const layout = {
            title: `Temperature Anomaly - ${result.times[timeIndex]}`,
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
        
        Plotly.newPlot(container, data, layout, {responsive: true});
    };
    
    // Create the initial plot
    createAnomalyPlot(0);
    
    // Add event listener for the time slider
    slider.addEventListener('input', function() {
        const timeIndex = parseInt(this.value);
        sliderValue.textContent = result.times[timeIndex];
        createAnomalyPlot(timeIndex);
    });
    
    // Add text summary
    const baselinePeriod = result.baseline_period || 'unknown';
    textResult.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-temperature-high me-2"></i>Temperature Anomaly Analysis</h5>
            </div>
            <div class="card-body">
                <p>The temperature anomaly analysis shows the deviation from a baseline period (${baselinePeriod}).</p>
                <p>Use the slider above to navigate through different time steps.</p>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Positive values (red) indicate warmer than baseline, negative values (blue) indicate cooler than baseline.
                </div>
            </div>
        </div>
    `;
}

/**
 * Display precipitation total analysis result
 * @param {HTMLElement} container - Result visualization container
 * @param {HTMLElement} textResult - Text result container
 * @param {Object} result - Analysis result data
 */
function displayPrecipitationTotal(container, textResult, result) {
    // Create a map visualization
    const data = [{
        type: 'contour',
        z: result.total_precipitation,
        x: result.longitudes[0],  // Assuming all rows have the same longitude values
        y: result.latitudes.map(row => row[0]),  // Get first column of latitudes
        colorscale: 'YlGnBu',
        contours: {
            coloring: 'heatmap',
            showlabels: true
        },
        colorbar: {
            title: `Precipitation (${result.units})`
        }
    }];
    
    const layout = {
        title: 'Total Precipitation',
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
    
    Plotly.newPlot(container, data, layout, {responsive: true});
    
    // Add text summary
    const precipitations = result.total_precipitation.flat();
    const validPrecip = precipitations.filter(p => !isNaN(p));
    const min = Math.min(...validPrecip).toFixed(2);
    const max = Math.max(...validPrecip).toFixed(2);
    const mean = (validPrecip.reduce((a, b) => a + b, 0) / validPrecip.length).toFixed(2);
    
    textResult.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-cloud-rain me-2"></i>Precipitation Summary</h5>
            </div>
            <div class="card-body">
                <p>The total precipitation analysis shows the cumulative precipitation across the spatial domain.</p>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Minimum</h6>
                                <p class="card-text display-6">${min}</p>
                                <p class="text-muted">${result.units}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Mean</h6>
                                <p class="card-text display-6">${mean}</p>
                                <p class="text-muted">${result.units}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Maximum</h6>
                                <p class="card-text display-6">${max}</p>
                                <p class="text-muted">${result.units}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Display climate indices analysis result
 * @param {HTMLElement} container - Result visualization container
 * @param {HTMLElement} textResult - Text result container
 * @param {Object} result - Analysis result data
 */
function displayClimateIndices(container, textResult, result) {
    // Check if there was an error in the index calculation
    if (result.error) {
        textResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error calculating climate index: ${result.error}
            </div>
        `;
        return;
    }
    
    // Create a map visualization
    const data = [{
        type: 'contour',
        z: result.index_values,
        x: result.longitudes[0],  // Assuming all rows have the same longitude values
        y: result.latitudes.map(row => row[0]),  // Get first column of latitudes
        colorscale: 'Viridis',
        contours: {
            coloring: 'heatmap',
            showlabels: true
        },
        colorbar: {
            title: result.index_type || 'Index Value'
        }
    }];
    
    const layout = {
        title: `Climate Index: ${result.index_type || 'Unknown'}`,
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
    
    Plotly.newPlot(container, data, layout, {responsive: true});
    
    // Add text summary
    const indexValues = result.index_values.flat();
    const validValues = indexValues.filter(v => !isNaN(v));
    const min = Math.min(...validValues).toFixed(2);
    const max = Math.max(...validValues).toFixed(2);
    const mean = (validValues.reduce((a, b) => a + b, 0) / validValues.length).toFixed(2);
    
    // Generate description based on index type
    let indexDescription = '';
    const indexType = result.index_type || '';
    
    if (indexType === 'FD') {
        indexDescription = 'Frost Days (FD) - Number of days when daily minimum temperature is below 0°C';
    } else if (indexType === 'SU') {
        indexDescription = 'Summer Days (SU) - Number of days when daily maximum temperature is above 25°C';
    } else if (indexType === 'ID') {
        indexDescription = 'Ice Days (ID) - Number of days when daily maximum temperature is below 0°C';
    } else if (indexType === 'GSL') {
        indexDescription = 'Growing Season Length (GSL) - Length of growing season';
    } else if (indexType === 'TXx') {
        indexDescription = 'Maximum of daily maximum temperature (TXx)';
    } else if (indexType === 'TNn') {
        indexDescription = 'Minimum of daily minimum temperature (TNn)';
    } else {
        indexDescription = result.description || 'Climate index measuring extreme or specific climate conditions';
    }
    
    textResult.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-chart-line me-2"></i>Climate Index Analysis</h5>
            </div>
            <div class="card-body">
                <p><strong>Index:</strong> ${indexType}</p>
                <p>${indexDescription}</p>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Minimum</h6>
                                <p class="card-text display-6">${min}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Mean</h6>
                                <p class="card-text display-6">${mean}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">Maximum</h6>
                                <p class="card-text display-6">${max}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Display seasonal cycle analysis result
 * @param {HTMLElement} container - Result visualization container
 * @param {HTMLElement} textResult - Text result container
 * @param {Object} result - Analysis result data
 */
function displaySeasonalCycle(container, textResult, result) {
    // Create monthly means array
    const months = result.months;
    
    // Extract data for plotting
    // For simplicity, we'll use the spatial average for each month
    const monthlyData = [];
    
    for (let m = 0; m < months.length; m++) {
        let sum = 0;
        let count = 0;
        
        for (let i = 0; i < result.monthly_means.length; i++) {
            for (let j = 0; j < result.monthly_means[i].length; j++) {
                if (!isNaN(result.monthly_means[i][j][m])) {
                    sum += result.monthly_means[i][j][m];
                    count++;
                }
            }
        }
        
        monthlyData.push(count > 0 ? sum / count : null);
    }
    
    // Create a time series plot
    const data = [{
        type: 'scatter',
        mode: 'lines+markers',
        x: months,
        y: monthlyData,
        line: {
            color: '#36B677',
            width: 2
        },
        marker: {
            color: '#36B677',
            size: 8
        }
    }];
    
    const layout = {
        title: 'Seasonal Cycle',
        xaxis: {
            title: 'Month'
        },
        yaxis: {
            title: `${result.units || 'Value'}`
        },
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50
        }
    };
    
    Plotly.newPlot(container, data, layout, {responsive: true});
    
    // Find maximum and minimum months
    const maxMonth = months[monthlyData.indexOf(Math.max(...monthlyData))];
    const minMonth = months[monthlyData.indexOf(Math.min(...monthlyData))];
    
    // Add text summary
    textResult.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-calendar-alt me-2"></i>Seasonal Cycle Analysis</h5>
            </div>
            <div class="card-body">
                <p>The seasonal cycle analysis shows the monthly pattern of the selected variable.</p>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Peak month:</strong> ${maxMonth} (${Math.max(...monthlyData).toFixed(2)} ${result.units || ''})
                    <br>
                    <strong>Minimum month:</strong> ${minMonth} (${Math.min(...monthlyData).toFixed(2)} ${result.units || ''})
                </div>
                <p>The seasonal variation is ${(Math.max(...monthlyData) - Math.min(...monthlyData)).toFixed(2)} ${result.units || ''}, 
                representing the difference between the maximum and minimum monthly values.</p>
            </div>
        </div>
    `;
}

/**
 * Update analysis statistics display
 * @param {Object} result - Analysis result to display stats for
 */
function updateAnalysisStats(result) {
    document.getElementById('stat-analysis-type').textContent = result.analysis_type || '-';
    document.getElementById('stat-variable').textContent = result.variable || '-';
    document.getElementById('stat-time').textContent = new Date().toLocaleString();
    
    // Set status
    const statusSpan = document.getElementById('stat-status');
    if (result.error) {
        statusSpan.textContent = 'Failed';
        statusSpan.className = 'badge bg-danger';
    } else {
        statusSpan.textContent = 'Completed';
        statusSpan.className = 'badge bg-success';
    }
}

/**
 * Show the export modal
 */
function showExportModal() {
    if (!currentAnalysis) {
        alert('No analysis results available to export');
        return;
    }
    
    // Set filename based on analysis type
    const analysisType = currentAnalysis.analysis_type || 'unknown';
    document.getElementById('export-filename').value = `climate_${analysisType}_${new Date().toISOString().slice(0, 10)}`;
    
    // Show modal
    const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
    exportModal.show();
}

/**
 * Export analysis results
 */
function exportResult() {
    if (!currentAnalysis) {
        alert('No analysis results available to export');
        return;
    }
    
    const format = document.getElementById('export-format').value;
    const filename = document.getElementById('export-filename').value;
    
    // Call server-side endpoint to generate export
    fetch(`/api/analysis/${currentAnalysisId}?format=${format}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Download the exported file
                downloadExportedFile(data.result.export_url, `${filename}.${format}`);
            } else {
                throw new Error(data.error || 'Export failed');
            }
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            alert(`Export failed: ${error.message}`);
        });
    
    // Close the modal
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
}

/**
 * Download an exported file
 * @param {string} url - URL of the file to download
 * @param {string} filename - Name to save the file as
 */
function downloadExportedFile(url, filename) {
    // Create a download link
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/**
 * Download the current visualization result as an image
 */
function downloadResult() {
    if (!currentAnalysis) {
        alert('No analysis results available to download');
        return;
    }
    
    const analysisType = currentAnalysis.analysis_type || 'unknown';
    const filename = `climate_${analysisType}_${new Date().toISOString().slice(0, 10)}`;
    
    // Use Plotly's built-in download functionality
    Plotly.downloadImage('analysis-result-visualization', {
        format: 'png',
        width: 1200,
        height: 800,
        filename: filename
    });
}
