# Setup


* Open the app "IP Webcam" on the smartphone.
* Scroll down and choose "Server starten" to start the webcam live-feed
   The feed can be stopped by "Aktionen" -> "Stop"
* Position the smartphone such that it covers the whole sheet and the circle on the sheet
* Run the following command
    ./circle.py -u http://10.6.233.126:8080/video
with the correct URL. You can obtain the URL from the smartphone (it is written in the lower half of the display)
* Check if there is output in the terminal showing pi
* Check if there appears a picture on the screen (takes a moment to appear)
* In a second terminal run
    ./gui.py
and check whether the picture and number change accordingly
* Alter the config.json file and see what happens. If there is a json-parse error the config is is not read, json is VERY strict. There are comments in the file
* Enable fun!

---

# Draw circles

4 circles:

    [210, 350, 110],
    [430, 350, 110],
    [210, 130, 110],
    [430, 130, 110]

9 circles:

    [180, 380, 70],
    [320, 380, 70],
    [460, 380, 70],
    [180, 240, 70],
    [320, 240, 70],
    [460, 240, 70],
    [180, 100, 70],
    [320, 100, 70],
    [460, 100, 70]

1 circle:

    [320, 240, 220]

16 circles:

    [155, 405, 55],
    [265, 405, 55],
    [375, 405, 55],
    [485, 405, 55],
    [155, 295, 55],
    [265, 295, 55],
    [375, 295, 55],
    [485, 295, 55],
    [155, 185, 55],
    [265, 185, 55],
    [375, 185, 55],
    [485, 185, 55],
    [155, 75, 55],
    [265, 75, 55],
    [375, 75, 55],
    [485, 75, 55]

---

# Misc

original call to HoughCircles():

    detect_circles = cv2.HoughCircles(image['circle'], cv2.HOUGH_GRADIENT, 1, 200,
        param1 = 30,
        param2 = 45, # the smaller, the more false circles may be detected
        minRadius = 50,
        maxRadius = 480
    )

original call to findContours():

    dots, hierarchy = cv2.findContours(image['dots'], cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) # find dots

original call to drawContours():

    cv2.drawContours(image['output'], dots_in_rect, -1, dot_color, cv2.FILLED)