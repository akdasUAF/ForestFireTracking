import cv2
import numpy as np

# Seven Rules for Segmentation -> https://core.ac.uk/download/pdf/55305301.pdf
def fire_pixel_segmentation(image):
    fire_mask = np.zeros_like(image[:, :, 0])
    
    # YCbCr Color Space and splitting BGR Channel
    YCrCb_im = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(YCrCb_im)
    B, G, R = cv2.split(image)
    
    # Rule 1: R > G > B
    mask1 = (R > G) & (G > B)
    
    # Rule 2: R > 190 & G > 100 & B < 140
    mask2 = (R > 190) & (G > 100) & (B < 140)
    
    # Rule 3 & 4: Y >= Cb & Cr >= Cb
    mask3_4 = (Y >= Cb) & (Cr >= Cb)
    
    # Rule 5: Y >= Ymean & Cb <= Cbmean & Cr >= Crmean
    mask5 = (Y >= np.mean(Y)) & (Cb <= np.mean(Cb)) & (Cr >= np.mean(Cr))
    
    # Rule 6: Cb-Cr >= 70 (Threshold)
    mask6 = abs(Cb-Cr) >= 70
    
    # Rule 7: Cb <= 120 & Cr >= 150
    mask7 = (Cb <= 120) & (Cr >= 150)

    combined_mask = mask1 & mask2 & mask3_4 & mask5 & mask6 & mask7
    fire_mask[combined_mask] = 255

    kernel = np.ones((3, 3), np.uint8)
    eroded_mask = cv2.erode(fire_mask, kernel, iterations=1)
    fire_mask = cv2.dilate(eroded_mask, kernel, iterations=1)
    
    return fire_mask

def calculate_gsd(object_distance, frame_width, sensor_width, focal_length):

    gsd = (sensor_width * object_distance) / (frame_width * focal_length)
    return gsd  # Returns meters per pixel

def fire_flow(fire_mask, area_frame, fireX, fireY, processed_frame, m, object_distance, frame_width, sensor_width, focal_length):
    # Get the ground sampling distance (meters per pixel)
    meters_per_pixel = calculate_gsd(object_distance, frame_width, sensor_width, focal_length)

    centerX = []
    centerY = []
    contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cv2.drawContours(processed_frame, contours, -1, (0, 0, 255), 2)  # Draw fire contours
    
    for contour in contours:
        area = cv2.contourArea(contour)

        M = cv2.moments(contour)
        if M["m00"] != 0 and area > 50:  # Ignore small noise areas
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            
            centerX.append(cX)
            centerY.append(cY)
            
    # Track fire centroid movement
    fireX.append(np.mean(centerX))
    fireY.append(np.mean(centerY))
    
    if len(fireX) > m:
        x = np.nanmean(fireX)
        y = np.nanmean(fireY)
        endpoint_mframes = (int(x), int(y)) if np.isfinite(x) and np.isfinite(y) else None
        fireX.pop(0)
        fireY.pop(0)
    else:
        endpoint_mframes = None

    # Total pixel area in THIS FRAME ONLY! Do not accumulate them...
    current_frame_pixels = sum(cv2.contourArea(contour) for contour in contours)

    # Convert to real-world area (in m^2)
    current_actual_area = current_frame_pixels * (meters_per_pixel ** 2)

    # Update cumulative area_frame
    cv2.drawContours(area_frame, contours, -1, (0, 0, 255), -1)

    # Display current frame area (not cumulative!)
    cv2.putText(processed_frame, f'Current Fire Area: {current_actual_area:.2f} m^2',
                (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return current_actual_area, area_frame, processed_frame, endpoint_mframes
