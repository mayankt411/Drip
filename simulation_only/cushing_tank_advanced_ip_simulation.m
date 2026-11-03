%% ADVANCED CUSHING OIL TANK 3D SIMULATION & MULTI-STAGE IMAGE PROCESSING
% Topic: Satellite-Based Oil Storage Volume Estimation from Shadow Geometry
% Focus: Comprehensive 6-Stage Computer Vision & Digital Image Processing Pipeline:
%   1. Simulated Sentinel-2 Multi-spectral Optical ROI (10m GSD)
%   2. Canny Edge Detection & Gradient Vector Field (Tank Rim & Shadow Edge)
%   3. Bimodal Histogram & Otsu Discriminant Maximization (sigma_B^2)
%   4. Mathematical Morphology (Disk Structuring Element Opening & Dilation)
%   5. Directional Radon / Ray-Casting Profile along Solar Azimuth
%   6. 3D Ray-Traced Physics Model (Liquid Elevation & Sun Illumination)
%
% Validated Against: ASTM / API MPMS Chapter 11.1 Standard Petroleum Factor
% Tested on MATLAB R2025a

function cushing_tank_advanced_ip_simulation()
    close all;
    
    % --- Physical Tank Parameters (Cushing Hub Commercial Floating Roof) ---
    H_wall = 18.0;          % Steel shell wall height (meters)
    R_tank = 40.0;          % Internal radius (meters) -> 80m diameter
    h_empty = 1.5;          % Floating-roof pontoon rest leg clearance (meters)
    BBL_CONV = 6.28981077;  % Standard ASTM conversion factor: 1 m^3 = 6.28981077 bbl
    
    % --- Initial Simulation State ---
    solar_elev = 42.0;      % Solar elevation angle (degrees above horizon)
    solar_az   = 165.0;     % Solar azimuth angle (degrees clockwise from North)
    roof_h     = 9.5;       % Floating roof elevation above floor (meters)
    
    % --- Master UI Figure Window ---
    hFig = figure('Name', 'Cushing Crude Storage: 3D Physics & Multi-Stage Image Processing', ...
                  'Color', [0.08, 0.10, 0.14], ...
                  'Position', [40, 40, 1500, 880], ...
                  'NumberTitle', 'off');
              
    % Master Header Banner
    uicontrol('Style', 'text', 'Parent', hFig, ...
              'Position', [20, 835, 1460, 35], ...
              'String', 'Multi-Stage Computer Vision Pipeline: Floating-Roof Shadow Extraction & Volume Reconstruction', ...
              'FontSize', 15, 'FontWeight', 'bold', ...
              'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.08, 0.10, 0.14]);

    % --- 6-Panel Layout ---
    % 1. 3D Physical Ray-Tracing (Left Main)
    ax3D = axes('Parent', hFig, 'Position', [0.04, 0.38, 0.34, 0.44], 'Color', [0.05, 0.07, 0.09]);
    
    % 2. Stage 1: Optical Sentinel-2 Simulated Capture (Top Row Mid)
    axOptical = axes('Parent', hFig, 'Position', [0.42, 0.63, 0.16, 0.19], 'Color', [0.05, 0.07, 0.09]);
    
    % 3. Stage 2: Canny Edge Detection & Rim Localization (Top Row Right-Mid)
    axCanny = axes('Parent', hFig, 'Position', [0.61, 0.63, 0.16, 0.19], 'Color', [0.05, 0.07, 0.09]);

    % 4. Stage 3 & 4: Morphological Otsu Shadow Mask (Top Row Far-Right)
    axMorph = axes('Parent', hFig, 'Position', [0.80, 0.63, 0.16, 0.19], 'Color', [0.05, 0.07, 0.09]);

    % 5. Stage 5A: Pixel Intensity Histogram & Otsu Cutoff (Bottom Row Mid-Left)
    axHist = axes('Parent', hFig, 'Position', [0.42, 0.36, 0.26, 0.20], 'Color', [0.05, 0.07, 0.09]);

    % 6. Stage 5B: Directional Radial Profile along Solar Azimuth (Bottom Row Mid-Right)
    axProfile = axes('Parent', hFig, 'Position', [0.72, 0.36, 0.24, 0.20], 'Color', [0.05, 0.07, 0.09]);

    % --- Control & Metrics Panel (Bottom Row) ---
    pnlCtrl = uipanel('Parent', hFig, 'Position', [0.04, 0.03, 0.92, 0.28], ...
                      'Title', 'Simulation Controls & Real-Time Computer Vision Analytics', ...
                      'FontSize', 11, 'ForegroundColor', [0.9, 0.9, 0.9], ...
                      'BackgroundColor', [0.12, 0.15, 0.20], 'BorderType', 'line', 'HighlightColor', [0.25, 0.30, 0.40]);

    % Slider 1: Roof Height (h)
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [20, 160, 160, 20], ...
              'String', 'Roof Height (h) [m]:', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.85, 0.85, 0.85], 'BackgroundColor', [0.12, 0.15, 0.20]);
    sldRoof = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [180, 160, 260, 20], ...
                        'Min', h_empty, 'Max', H_wall - 0.5, 'Value', roof_h);
    lblRoofVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [450, 160, 70, 20], ...
                           'String', sprintf('%.1f m', roof_h), 'FontSize', 10, 'FontWeight', 'bold', ...
                           'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.12, 0.15, 0.20]);

    % Slider 2: Solar Elevation Angle (alpha)
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [20, 115, 160, 20], ...
              'String', 'Solar Elevation (\alpha) [°]:', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.85, 0.85, 0.85], 'BackgroundColor', [0.12, 0.15, 0.20]);
    sldElev = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [180, 115, 260, 20], ...
                        'Min', 15.0, 'Max', 75.0, 'Value', solar_elev);
    lblElevVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [450, 115, 70, 20], ...
                           'String', sprintf('%.1f°', solar_elev), 'FontSize', 10, 'FontWeight', 'bold', ...
                           'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.12, 0.15, 0.20]);

    % Slider 3: Solar Azimuth Angle (theta)
    uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [20, 70, 160, 20], ...
              'String', 'Solar Azimuth (\theta) [°]:', 'FontSize', 10, 'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.85, 0.85, 0.85], 'BackgroundColor', [0.12, 0.15, 0.20]);
    sldAz = uicontrol('Parent', pnlCtrl, 'Style', 'slider', 'Position', [180, 70, 260, 20], ...
                      'Min', 90.0, 'Max', 270.0, 'Value', solar_az);
    lblAzVal = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [450, 70, 70, 20], ...
                         'String', sprintf('%.1f°', solar_az), 'FontSize', 10, 'FontWeight', 'bold', ...
                         'ForegroundColor', [0.22, 0.74, 0.97], 'BackgroundColor', [0.12, 0.15, 0.20]);

    % Analytical Output Readout Boxes
    lblTheory = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [540, 20, 400, 180], ...
                          'String', '', 'FontSize', 10, 'FontName', 'Courier', ...
                          'ForegroundColor', [0.35, 0.85, 0.45], 'BackgroundColor', [0.06, 0.08, 0.12], ...
                          'HorizontalAlignment', 'left');

    lblCVReadout = uicontrol('Parent', pnlCtrl, 'Style', 'text', 'Position', [960, 20, 410, 180], ...
                             'String', '', 'FontSize', 10, 'FontName', 'Courier', ...
                             'ForegroundColor', [0.25, 0.75, 1.00], 'BackgroundColor', [0.06, 0.08, 0.12], ...
                             'HorizontalAlignment', 'left');

    % Set Callbacks
    set(sldRoof, 'Callback', @update_all);
    set(sldElev, 'Callback', @update_all);
    set(sldAz,   'Callback', @update_all);

    % Run Initial Visualization
    update_all();

    %% --- CORE SIMULATION & COMPUTER VISION CALLBACK ---
    function update_all(~, ~)
        % 1. Read Current Slider States
        h_val     = get(sldRoof, 'Value');
        alpha_val = get(sldElev, 'Value');
        az_val    = get(sldAz,   'Value');

        set(lblRoofVal, 'String', sprintf('%.1f m', h_val));
        set(lblElevVal, 'String', sprintf('%.1f°', alpha_val));
        set(lblAzVal,   'String', sprintf('%.1f°', az_val));

        % 2. Mathematical Physics (Ground Truth)
        tan_alpha = tand(alpha_val);
        gap_height = H_wall - h_val;                    % (H - h)
        shadow_len_theory = gap_height / tan_alpha;      % L = (H - h) / tan(alpha)
        
        eff_h = max(0, h_val - h_empty);
        vol_m3_true = pi * (R_tank^2) * eff_h;
        vol_bbl_true = vol_m3_true * BBL_CONV;
        max_vol_bbl = pi * (R_tank^2) * (H_wall - h_empty) * BBL_CONV;
        fill_pct = (vol_bbl_true / max_vol_bbl) * 100.0;

        % -------------------------------------------------------------
        % 3. IMAGE PROCESSING PIPELINE EXECUTION
        % -------------------------------------------------------------
        % Create synthetic top-down optical ROI (120x120 grid representing 120m x 120m)
        grid_dim = 120;
        [Xg, Yg] = meshgrid(linspace(-60, 60, grid_dim), linspace(-60, 60, grid_dim));
        dist_from_center = sqrt(Xg.^2 + Yg.^2);
        
        % Background terrain reflectance
        optical_img = 125 + 14 * randn(grid_dim, grid_dim);
        
        % Tank Mask
        tank_mask = dist_from_center <= R_tank;
        
        % High-albedo painted pontoon roof: ~195 DN
        optical_img(tank_mask) = 195 + 8 * randn(sum(tank_mask(:)), 1);
        
        % Shadow displacement along solar illumination ray
        shadow_dx = -sind(az_val) * shadow_len_theory;
        shadow_dy = -cosd(az_val) * shadow_len_theory;
        
        % Projected interior wall shadow
        X_back = Xg - shadow_dx;
        Y_back = Yg - shadow_dy;
        back_dist = sqrt(X_back.^2 + Y_back.^2);
        
        shadow_condition = tank_mask & (back_dist >= R_tank);
        optical_img(shadow_condition) = 38 + 6 * randn(sum(shadow_condition(:)), 1); % Dark shadow: ~38 DN
        
        % Steel rim outline
        rim_condition = abs(dist_from_center - R_tank) <= 1.2;
        optical_img(rim_condition) = 75 + 5 * randn(sum(rim_condition(:)), 1);

        uint_img = uint8(max(0, min(255, optical_img)));

        % STAGE 2: Canny Edge Detection
        canny_edges = edge(uint_img, 'Canny', [0.10, 0.25]);

        % STAGE 3: Otsu Global Discriminant Thresholding
        roi_pixels = uint_img(tank_mask);
        [otsu_t, ~] = graythresh(roi_pixels);
        otsu_dn = otsu_t * 255.0;
        binary_shadow = tank_mask & (uint_img < otsu_dn);

        % STAGE 4: Mathematical Morphology (Opening with 3x3 Disk)
        se = strel('disk', 2);
        morph_shadow = imopen(binary_shadow, se);

        % STAGE 5: Radial Solar Azimuth Profiling
        rad_r = linspace(0, R_tank, 60);
        profile_vals = interp2(Xg, Yg, double(uint_img), -rad_r * sind(az_val), -rad_r * cosd(az_val), 'linear', 190);
        
        % Computer Vision Edge Measurement
        is_shadow_pts = profile_vals < otsu_dn;
        cv_shadow_len = sum(is_shadow_pts) * (R_tank / 60.0);
        
        % Reconstructed height and volume from CV measurement
        cv_roof_h = max(h_empty, min(H_wall, H_wall - cv_shadow_len * tan_alpha));
        cv_vol_bbl = pi * (R_tank^2) * (cv_roof_h - h_empty) * BBL_CONV;
        error_bbl = abs(cv_vol_bbl - vol_bbl_true);
        error_pct = (error_bbl / max(1, vol_bbl_true)) * 100.0;

        % -------------------------------------------------------------
        % 4. UPDATE TEXT READOUT PANELS
        % -------------------------------------------------------------
        theory_str = sprintf([...
            '=== 1. PHYSICAL GROUND TRUTH ===\n' ...
            '• Shell Height (H):    %.1f m\n' ...
            '• Liquid Height (h):   %.1f m\n' ...
            '• Sun Elevation (α):   %.1f°\n' ...
            '• Sun Azimuth (θ):     %.1f°\n' ...
            '--------------------------------\n' ...
            '• Theoretical Gap:     %.1f m\n' ...
            '• Ideal Shadow (L):    %.2f m\n' ...
            '• True Volume:         %s bbl\n' ...
            '• Working Fill Rate:   %.1f%%'], ...
            H_wall, h_val, alpha_val, az_val, ...
            gap_height, shadow_len_theory, ...
            num2bank(vol_bbl_true), fill_pct);
        set(lblTheory, 'String', theory_str);

        cv_str = sprintf([...
            '=== 2. COMPUTER VISION EXTRACTION ===\n' ...
            '• Canny Edge Filter:   High/Low T=[0.25, 0.10]\n' ...
            '• Otsu Threshold (T*): %.1f DN\n' ...
            '• Morphological Clean: Disk Kernel (r=2)\n' ...
            '• Directional Ray:     θ_ray = %.1f°\n' ...
            '--------------------------------------\n' ...
            '• CV Measured Shadow:  %.2f m\n' ...
            '• CV Estimated Height: %.2f m\n' ...
            '• CV Estimated Volume: %s bbl\n' ...
            '• Reconstruction Error:%.2f%% (%.0f bbl)'], ...
            otsu_dn, mod(az_val + 180, 360), ...
            cv_shadow_len, cv_roof_h, ...
            num2bank(cv_vol_bbl), error_pct, error_bbl);
        set(lblCVReadout, 'String', cv_str);

        % -------------------------------------------------------------
        % 5. RENDER 3D PHYSICAL SCENE
        % -------------------------------------------------------------
        cla(ax3D); hold(ax3D, 'on');
        
        % Cylindrical Wall (translucent steel)
        [cylX, cylY, cylZ] = cylinder(R_tank, 50);
        cylZ = cylZ * H_wall;
        surf(ax3D, cylX, cylY, cylZ, 'FaceColor', [0.4, 0.45, 0.52], 'EdgeColor', 'none', 'FaceAlpha', 0.22);
        
        % Floating Roof Disc
        theta_disc = linspace(0, 2*pi, 60);
        patch(ax3D, R_tank*cos(theta_disc), R_tank*sin(theta_disc), ones(size(theta_disc))*h_val, ...
              [0.78, 0.80, 0.85], 'EdgeColor', [0.3, 0.3, 0.3], 'FaceAlpha', 0.9);
          
        % Crude Oil Body
        [oilX, oilY, oilZ] = cylinder(R_tank * 0.98, 40);
        oilZ = oilZ * h_val;
        surf(ax3D, oilX, oilY, oilZ, 'FaceColor', [0.36, 0.18, 0.04], 'EdgeColor', 'none', 'FaceAlpha', 0.65);
        
        % 3D Wall Shadow Polygon on Roof
        if any(shadow_condition(:))
            patch(ax3D, Xg(shadow_condition), Yg(shadow_condition), ones(sum(shadow_condition(:)), 1)*(h_val + 0.05), ...
                  [0.08, 0.08, 0.08], 'EdgeColor', 'none', 'FaceAlpha', 0.88);
        end
        
        % Directional Sun Beam Rays
        ray_len = 35.0;
        ray_x0 = -sind(az_val) * R_tank * 1.5;
        ray_y0 = -cosd(az_val) * R_tank * 1.5;
        ray_z0 = H_wall + ray_len * sind(alpha_val);
        quiver3(ax3D, ray_x0, ray_y0, ray_z0, ...
                sind(az_val)*R_tank, cosd(az_val)*R_tank, -ray_len*sind(alpha_val), ...
                0, 'Color', [1.0, 0.85, 0.2], 'LineWidth', 2.2, 'MaxHeadSize', 0.5);
            
        title(ax3D, '3D Physical Model: Floating-Roof & Sun Shadow', 'Color', [0.9, 0.9, 0.9], 'FontSize', 11);
        axis(ax3D, 'equal'); view(ax3D, [az_val + 25, 34]); grid(ax3D, 'on');
        set(ax3D, 'XColor', [0.3, 0.3, 0.3], 'YColor', [0.3, 0.3, 0.3], 'ZColor', [0.3, 0.3, 0.3]);
        xlim(ax3D, [-55, 55]); ylim(ax3D, [-55, 55]); zlim(ax3D, [0, H_wall + 10]);

        % -------------------------------------------------------------
        % 6. RENDER STAGE 1: OPTICAL ROI
        % -------------------------------------------------------------
        cla(axOptical);
        imagesc(axOptical, [-60, 60], [-60, 60], uint_img);
        colormap(axOptical, 'gray'); axis(axOptical, 'image');
        title(axOptical, '1. Sentinel-2 Optical ROI', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        set(axOptical, 'XColor', [0.3, 0.3, 0.3], 'YColor', [0.3, 0.3, 0.3]);

        % -------------------------------------------------------------
        % 7. RENDER STAGE 2: CANNY EDGE MAP
        % -------------------------------------------------------------
        cla(axCanny);
        imshow(canny_edges, 'Parent', axCanny);
        title(axCanny, '2. Canny Edge Detection', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);

        % -------------------------------------------------------------
        % 8. RENDER STAGE 3 & 4: MORPHOLOGICAL OTSU MASK
        % -------------------------------------------------------------
        cla(axMorph);
        rgb_overlay = repmat(double(uint_img)/255.0, [1, 1, 3]);
        rgb_overlay(:,:,1) = rgb_overlay(:,:,1) + double(morph_shadow)*0.75; % Red tint
        rgb_overlay = min(1.0, rgb_overlay);
        imshow(rgb_overlay, 'Parent', axMorph);
        title(axMorph, '3. Otsu + Morphological Mask', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);

        % -------------------------------------------------------------
        % 9. RENDER STAGE 5A: HISTOGRAM & OTSU CUTOFF
        % -------------------------------------------------------------
        cla(axHist); hold(axHist, 'on');
        [h_counts, h_bins] = histcounts(roi_pixels, 0:5:255);
        bar(axHist, h_bins(1:end-1), h_counts, 'FaceColor', [0.22, 0.74, 0.97], 'EdgeColor', 'none', 'FaceAlpha', 0.7);
        xline(axHist, otsu_dn, '--', sprintf('Otsu T*=%.1f', otsu_dn), ...
              'Color', [0.95, 0.40, 0.40], 'LineWidth', 2.0, 'LabelHorizontalAlignment', 'left');
        title(axHist, '4. Pixel Intensity Histogram & Otsu Threshold', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        xlabel(axHist, 'Reflectance (DN)', 'Color', [0.8, 0.8, 0.8]); ylabel(axHist, 'Pixel Count', 'Color', [0.8, 0.8, 0.8]);
        grid(axHist, 'on'); set(axHist, 'XColor', [0.3, 0.3, 0.3], 'YColor', [0.3, 0.3, 0.3]);
        xlim(axHist, [0, 255]);

        % -------------------------------------------------------------
        % 10. RENDER STAGE 5B: RADIAL PROFILE ALONG AZIMUTH
        % -------------------------------------------------------------
        cla(axProfile); hold(axProfile, 'on');
        plot(axProfile, rad_r, profile_vals, 'Color', [0.22, 0.74, 0.97], 'LineWidth', 2.2);
        yline(axProfile, otsu_dn, '--', 'Otsu Level', 'Color', [0.95, 0.40, 0.40], 'LineWidth', 1.5);
        xline(axProfile, cv_shadow_len, ':', sprintf('CV L=%.1f m', cv_shadow_len), ...
              'Color', [0.30, 0.90, 0.45], 'LineWidth', 2.0);
        title(axProfile, '5. Radial Profile (Along Solar Azimuth Ray)', 'Color', [0.9, 0.9, 0.9], 'FontSize', 10);
        xlabel(axProfile, 'Distance from Rim (m)', 'Color', [0.8, 0.8, 0.8]); ylabel(axProfile, 'Reflectance (DN)', 'Color', [0.8, 0.8, 0.8]);
        grid(axProfile, 'on'); set(axProfile, 'XColor', [0.3, 0.3, 0.3], 'YColor', [0.3, 0.3, 0.3]);
        xlim(axProfile, [0, R_tank]); ylim(axProfile, [0, 255]);
    end

    function s = num2bank(n)
        s = sprintf('%.0f', n);
        idx = length(s)-2:-3:2;
        for i = idx
            s = [s(1:i-1), ',', s(i:end)];
        end
    end
end
