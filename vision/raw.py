import cv2
import numpy as np

def detect_sidewalk_edges(image_path):
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not load image.")
        return
    
    # Resize for consistency
    image = cv2.resize(image, (800, 600))

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian Blur to smooth the image and reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny Edge Detection
    edges = cv2.Canny(blurred, 50, 150)

    # Apply Hough Line Transform to detect straight edges (potential sidewalk edges)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=100, maxLineGap=50)

    # Draw detected lines on the original image
    result = image.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(result, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red lines for sidewalk edges

    # Display the images
    cv2.imshow("Original Image", image)
    cv2.imshow("Edges Detected", edges)
    cv2.imshow("Sidewalk Edges", result)

    # Save the result
    cv2.imwrite("sidewalk_edges_hough.png", result)
    print("Sidewalk edge detection saved as 'sidewalk_edges_hough.png'")

    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage: replace 'sidewalk.jpg' with your actual image path
detect_sidewalk_edges("track.jpg")
