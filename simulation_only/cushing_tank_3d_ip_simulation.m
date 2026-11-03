%% CUSHING OIL STORAGE TANK: 3D SIMULATION & IMAGE PROCESSING PIPELINE
% Topic: Satellite-Based Oil Storage Volume Estimation from Shadow Geometry
% Focus: Digital Image Processing (Otsu Thresholding, Morphology, Radial Profiling)
% Validated Against: ASTM / API mpms Ch 11.1 Standard Conversion Factor
%
% Run this script in MATLAB R2025a. It launches an interactive 3D GUI simulation.

function cushing_tank_3d_ip_simulation()
    close all;
    
    % --- Tank Physical Parameters (Cushing Hub Standard) ---
    H_wall = 18.0;          % Wall height (meters)
    R_tank = 40.0;          % Tank radius (meters)
    h_empty = 1.5;          % Floating-roof grounded pontoon height (m)
    BBL_CONV = 6.28981077;  % 1 m^3 = 6.28981077 barrels (ASTM standard)
    GSD = 10.0;             % Sentinel-2 Ground Sample Distance (10m / pixel)
    
    % --- Initial State ---
    solar_elev = 42.0;      % Solar elevation angle (degrees)
    solar_az   = 165.0;     % Solar azimuth angle (degrees)
    roof_h     = 9.5;       % Roof elevation above floor (meters)
    
    % --- Create Master UI Figure ---
    hFig = figure('Name', 'Cushing Oil Tank: 3D Physics & Image Processing Pipeline', ...
                  'Color', [0.10, 0.12, 0.16], ...
                  'Position', [80, 60, 1380, 820], ...
                  'NumberTitle', 'off');
              
    % Title Banner
    uicontrol('Style', 'text', 'Parent', hFig, ...
              'Position', [20, 775, 1340, 35], ...
              'String', 'Sentinel-2 Image Processing & 3D Shadow Trigonometry: Cushing Crude Storage Hub', ...
              'FontSize', 15, 'FontWeight', 'bold', ...
              'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.10, 0.12, 0.16]);
          
    % --- Subplot Layout (4 Core Views) ---
    % 1. 3D Physical Geometry (Upper Left)
    ax3D = axes('Parent', hFig, 'Position', [0.05, 0.38, 0.42, 0.54], 'Color', [0.06, 0.08, 0.11]);
    
    % 2. Simulated Sentinel-2 Top-Down Optical Capture (Upper Right Left)
    axOptical = axes('Parent', hFig, 'Position', [0.52, 0.58, 0.21, 0.34], 'Color', [0.06, 0.08, 0.11]);
    
    % 3. Image Processing: Otsu Segmentation & Morphology (Upper Right Right)
    axSegment = axes('Parent', hFig, 'Position', [0.76, 0.58, 0.21, 0.34], 'Color', [0.06, 0.08, 0.11]);
    
    % 4. Radial Solar Azimuth Intensity Profile (Lower Right)
    axProfile = axes('Parent', hFig, 'Position', [0.52, 0.20, 0.45, 0.30], 'Color', [0.06, 0.08, 0.11]);
    
    % --- Control & Metrics Panel (Bottom Left) ---
    pnlCtrl = uipanel('Parent', hFig, 'Position', [0.05, 0.04, 0.42, 0.30], ...
                      'Title', 'Simulation Controls & Geometric Physics', ...
                      'FontSize', 11, 'ForegroundColor', [0.9, 0.9, 0.9], ...
                      'BackgroundColor', [0.14, 0.17, 0.23], 'BorderType', 'line', 'HighlightColor', [0.25, 0.30, 0.40]);
                  
    % Slider: Roof Level
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [15, 175, 150, 20], ...
              'String', 'Roof Height (h):', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.8, 0.8, 0.8], 'BackgroundColor', [0.14, 0.17, 0.23]);
    sldRoof = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [160, 175, 260, 20], ...
                        'Min', h_empty, 'Max', H_wall - 0.5, 'Value', roof_h);
    lblRoofVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [430, 175, 80, 20], ...
                           'String', sprintf('%.1f m', roof_h), 'FontSize', 10, 'FontWeight', 'bold', ...
                           'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.14, 0.17, 0.23]);
                       
    % Slider: Solar Elevation Angle
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [15, 135, 150, 20], ...
              'String', 'Solar Elevation (\alpha):', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.8, 0.8, 0.8], 'BackgroundColor', [0.14, 0.17, 0.23]);
    sldElev = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [160, 135, 260, 20], ...
                        'Min', 15.0, 'Max', 75.0, 'Value', solar_elev);
    lblElevVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [430, 135, 80, 20], ...
                           'String', sprintf('%.1f°', solar_elev), 'FontSize', 10, 'FontWeight', 'bold', ...
                           'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.14, 0.17, 0.23]);

    % Slider: Solar Azimuth Angle
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [15, 95, 150, 20], ...
              'String', 'Solar Azimuth (\theta):', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.8, 0.8, 0.8], 'BackgroundColor', [0.14, 0.17, 0.23]);
    sldAz = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [160, 95, 260, 20], ...
                      'Min', 90.0, 'Max', 270.0, 'Value', solar_az);
    lblAzVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [430, 95, 80, 20], ...
                         'String', sprintf('%.1f°', solar_az), 'FontSize', 10, 'FontWeight', 'bold', ...
                         'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.14, 0.17, 0.23]);

    % Computed Results Display Panel
    lblMetrics = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [15, 10, 520, 70], ...
                           'String', '', 'FontSize', 10, 'FontName', 'Courier', ...
                           'ForegroundColor', [0.3, 0.9, 0.4], 'BackgroundColor', [0.08, 0.10, 0.14], ...
                           'HorizontalAlignment', 'left');

    % Set Slider Callbacks
    set(sldRoof, 'Callback', @update_all);
    set(sldElev, 'Callback', @update_all);
    set(sldAz,   'Callback', @update_all);
    
    % Initial Draw
    update_all();
    
    %% --- MASTER UPDATE CALLBACK ---
    function update_all(~, ~)
        % Read UI state
        h_val = get(sldRoof, 'Value');
        alpha_val = get(sldElev, 'Value');
        az_val = get(sldAz, 'Value');
        
        set(lblRoofVal, 'String', sprintf('%.1f m', h_val));
        set(lblElevVal, 'String', sprintf('%.1f°', alpha_val));
        set(lblAzVal, 'String', sprintf('%.1f°', az_val));
        
        % 1. Physics Calculations
        tan_alpha = tand(alpha_val);
        gap_height = H_wall - h_val;                    % (H - h)
        shadow_len_ideal = gap_height / tan_alpha;       % L = (H - h) / tan(alpha)
        
        % Effective Volume
        eff_h = max(0, h_val - h_empty);
        vol_m3 = pi * (R_tank^2) * eff_h;
        vol_bbl = vol_m3 * BBL_CONV;
        max_vol_bbl = pi * (R_tank^2) * (H_wall - h_empty) * BBL_CONV;
        fill_pct = (vol_bbl / max_vol_bbl) * 100.0;
        
        % -------------------------------------------------------------
        % 2. IMAGE PROCESSING PIPELINE
        % -------------------------------------------------------------
        % Create synthetic top-down optical grid (simulating Sentinel-2 10m GSD ROI)
        grid_dim = 120; % 120x120 pixels representing 120m x 120m AOI (1m resolution for sub-pixel testing)
        [Xg, Yg] = meshgrid(linspace(-60, 60, grid_dim), linspace(-60, 60, grid_dim));
        dist_from_center = sqrt(Xg.^2 + Yg.^2);
        
        % Background terrain reflectance
        optical_img = 120 + 15 * randn(grid_dim, grid_dim); % surrounding ground
        
        % Inside Tank Mask
        tank_mask = dist_from_center <= R_tank;
        
        % Floating roof surface (high albedo painted steel: ~190 DN)
        optical_img(tank_mask) = 195 + 8 * randn(sum(tank_mask(:)), 1);
        
        % Projected Wall Shadow Polygon
        % Sun direction vector on ground:
        sun_dx = sind(az_val);
        sun_dy = cosd(az_val);
        
        % Points inside tank that fall in the shadow of the rim
        % Shadow displacement along solar azimuth:
        shadow_dx = -sind(az_val) * shadow_len_ideal;
        shadow_dy = -cosd(az_val) * shadow_len_ideal;
        
        % Check if a point's back-projection hits the rim
        X_back = Xg - shadow_dx;
        Y_back = Yg - shadow_dy;
        back_dist = sqrt(X_back.^2 + Y_back.^2);
        
        shadow_condition = tank_mask & (back_dist >= R_tank);
        optical_img(shadow_condition) = 38 + 6 * randn(sum(shadow_condition(:)), 1); % Dark interior shadow: ~38 DN
        
        % Add sensor noise and clip
        optical_img = max(0, min(255, optical_img));
        uint_img = uint8(optical_img);
        
        % Step 2A: Otsu Thresholding on Tank ROI
        roi_pixels = uint_img(tank_mask);
        [otsu_t, ~] = graythresh(roi_pixels); % Normalized Otsu threshold [0, 1]
        otsu_dn = otsu_t * 255.0;
        
        % Binary segmentation: Shadow = pixels below threshold
        segmented_shadow = tank_mask & (uint_img < otsu_dn);
        
        % Step 2B: Morphological Clean (Opening with disk kernel)
        se = strel('disk', 2);
        morph_shadow = imopen(segmented_shadow, se);
        
        % Step 2C: Radial Profile along Solar Azimuth
        rad_r = linspace(0, R_tank, 60);
        rad_x = R_tank - rad_r * sind(az_val);
        rad_y = R_tank - rad_r * cosd(az_val);
        profile_vals = interp2(Xg, Yg, double(uint_img), -rad_r * sind(az_val), -rad_r * cosd(az_val), 'linear', 190);
        
        % Reconstructed Shadow Length from Image Processing (edge detection drop)
        is_shadow_pts = profile_vals < otsu_dn;
        ip_shadow_len = sum(is_shadow_pts) * (R_tank / 60.0);
        
        % Reconstructed height from IP measurement: h_reconstructed = H - L_ip * tan(alpha)
        h_reconstructed = H_wall - ip_shadow_len * tan_alpha;
        vol_reconstructed_bbl = pi * (R_tank^2) * max(0, h_reconstructed - h_empty) * BBL_CONV;
        ip_error_bbl = abs(vol_reconstructed_bbl - vol_bbl);
        ip_error_pct = (ip_error_bbl / vol_bbl) * 100.0;
        
        % Update Status Label
        status_str = sprintf([...
            '--- SHADOW TRIGONOMETRY ---\n' ...
            'Theoretical Shadow: L = (%.1f-%.1f)/tan(%.1f°) = %.2f m\n' ...
            'Liquid Volume (bbl): %s bbl (%.1f%% Fill)\n\n' ...
            '--- IMAGE PROCESSING EXTRACTION ---\n' ...
            'Otsu Threshold Cutoff: %.1f DN (Separating Shadow / Roof)\n' ...
            'CV Measured Shadow:    %.2f m (Discretized Profile)\n' ...
            'IP Estimated Volume:   %s bbl (Error: %.2f%%)'], ...
            H_wall, h_val, alpha_val, shadow_len_ideal, ...
            num2bank(vol_bbl), fill_pct, ...
            otsu_dn, ip_shadow_len, ...
            num2bank(vol_reconstructed_bbl), ip_error_pct);
        set(lblMetrics, 'String', status_str);
        
        % -------------------------------------------------------------
        % 3. RENDER 3D PHYSICAL TANK
        % -------------------------------------------------------------
        cla(ax3D);
        hold(ax3D, 'on');
        
        % Outer Cylindrical Shell
        [cylX, cylY, cylZ] = cylinder(R_tank, 50);
        cylZ = cylZ * H_wall;
        surf(ax3D, cylX, cylY, cylZ, 'FaceColor', [0.4, 0.45, 0.52], 'EdgeColor', 'none', 'FaceAlpha', 0.25);
        
        % Floating Roof Disc
        theta = linspace(0, 2*pi, 60);
        discX = R_tank * cos(theta);
        discY = R_tank * sin(theta);
        discZ = ones(size(discX)) * h_val;
        patch(ax3D, discX, discY, discZ, [0.75, 0.78, 0.82], 'EdgeColor', [0.2, 0.2, 0.2], 'FaceAlpha', 0.9);
        
        % Crude Oil Body (from 0 to h_val)
        [oilX, oilY, oilZ] = cylinder(R_tank * 0.98, 40);
        oilZ = oilZ * h_val;
        surf(ax3D, oilX, oilY, oilZ, 'FaceColor', [0.35, 0.18, 0.05], 'EdgeColor', 'none', 'FaceAlpha', 0.6);
        
        % 3D Projected Wall Shadow on Roof
        roof_grid_pts = tank_mask & shadow_condition;
        if any(roof_grid_pts(:))
            patch(ax3D, Xg(shadow_condition), Yg(shadow_condition), ones(sum(shadow_condition(:)), 1) * (h_val + 0.05), ...
                  [0.08, 0.08, 0.08], 'EdgeColor', 'none', 'FaceAlpha', 0.85);
        end
        
        % Sun Beam Rays (Yellow Directional Vectors)
        sun_len = 35.0;
        ray_start_x = -sind(az_val) * R_tank * 1.5;
        ray_start_y = -cosd(az_val) * R_tank * 1.5;
        ray_start_z = H_wall + sun_len * sind(alpha_val);
        quiver3(ax3D, ray_start_x, ray_start_y, ray_start_z, ...
                sind(az_val)*R_tank, cosd(az_val)*R_tank, -sun_len*sind(alpha_val), ...
                0, 'Color', [1.0, 0.85, 0.2], 'LineWidth', 2.0, 'MaxHeadSize', 0.5);
            
        title(ax3D, '3D Physical Model: Floating-Roof & Sun Shadow', 'Color', [0.9, 0.9, 0.9], 'FontSize', 11);
        axis(ax3D, 'equal');
        view(ax3D, [az_val + 20, 32]);
        grid(ax3D, 'on');
        set(ax3D, 'XColor', [0.4, 0.4, 0.4], 'YColor', [0.4, 0.4, 0.4], 'ZColor', [0.4, 0.4, 0.4]);
        xlabel(ax3D, 'X (m)'); ylabel(ax3D, 'Y (m)'); zlabel(ax3D, 'Height (m)');
        xlim(ax3D, [-55, 55]); ylim(ax3D, [-55, 55]); zlim(ax3D, [0, H_wall + 10]);
        
        % -------------------------------------------------------------
        % 4. RENDER TOP-DOWN SIMULATED OPTICAL CAPTURE
        % -------------------------------------------------------------
        cla(axOptical);
        imagesc(axOptical, [-60, 60], [-60, 60], uint_img);
        colormap(axOptical, 'gray');
        axis(axOptical, 'image');
        title(axOptical, 'Sentinel-2 Top-Down Optical ROI', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        set(axOptical, 'XColor', [0.4, 0.4, 0.4], 'YColor', [0.4, 0.4, 0.4]);
        
        % -------------------------------------------------------------
        % 5. RENDER OTSU + MORPHOLOGICAL SEGMENTATION
        % -------------------------------------------------------------
        cla(axSegment);
        % Red overlay on segmented shadow
        seg_rgb = zeros(grid_dim, grid_dim, 3);
        seg_rgb(:,:,1) = double(uint_img)/255.0;
        seg_rgb(:,:,2) = double(uint_img)/255.0;
        seg_rgb(:,:,3) = double(uint_img)/255.0;
        
        % Highlight detected shadow in Cyan/Red
        seg_rgb(:,:,1) = seg_rgb(:,:,1) + double(morph_shadow)*0.7;
        seg_rgb = min(1.0, seg_rgb);
        
        imshow(seg_rgb, 'Parent', axSegment);
        title(axSegment, 'Otsu + Morphological Shadow Mask', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        
        % -------------------------------------------------------------
        % 6. RENDER RADIAL PROFILE ALONG SOLAR AZIMUTH
        % -------------------------------------------------------------
        cla(axProfile);
        hold(axProfile, 'on');
        plot(axProfile, rad_r, profile_vals, 'Color', [0.22, 0.74, 0.97], 'LineWidth', 2.0);
        yline(axProfile, otsu_dn, '--', sprintf('Otsu Cutoff (%.1f DN)', otsu_dn), ...
              'Color', [0.95, 0.4, 0.4], 'LineWidth', 1.5, 'LabelHorizontalAlignment', 'left');
        xline(axProfile, ip_shadow_len, ':', sprintf('Measured L: %.1f m', ip_shadow_len), ...
              'Color', [0.3, 0.9, 0.4], 'LineWidth', 1.5);
          
        title(axProfile, 'Radial Pixel Intensity Profile (Along Solar Azimuth Vector)', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        xlabel(axProfile, 'Distance from Outer Tank Rim (m)', 'Color', [0.8, 0.8, 0.8]);
        ylabel(axProfile, 'Pixel Reflectance (DN)', 'Color', [0.8, 0.8, 0.8]);
        grid(axProfile, 'on');
        set(axProfile, 'XColor', [0.4, 0.4, 0.4], 'YColor', [0.4, 0.4, 0.4]);
        ylim(axProfile, [0, 255]);
        xlim(axProfile, [0, R_tank]);
    end

    function s = num2bank(n)
        s = sprintf('%.0f', n);
        idx = length(s)-2:-3:2;
        for i = idx
            s = [s(1:i-1), ',', s(i:end)];
        end
    end
end
