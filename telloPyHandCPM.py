import sys
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import time
from imageAnalysis import handTracking
import pygame

# image resize parameters
width = 480
height = 360

# flag for saving video
SAVE_VIDEO = True


def show_image(img):
    cv2.imshow('IPWebcam', img)
    cv2.waitKey(1)


def computer_center_points(x, y, w, h, img):
    height = numpy.size(img, 0)
    width = numpy.size(img, 1)
    centerX = x + w / 2 - width / 2
    centerY = y + h / 2 - height / 2
    return centerX, centerY


def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))


def main():
    handTracking.init_cpm_session()
    drone = tellopy.Tello()

    try:
        pygame.init()
        pygame.display.set_mode((1, 1))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output.avi', fourcc, 15.0, (960, 720))
        drone.connect()
        drone.wait_for_connection(60.0)

        container = av.open(drone.get_video_stream())
        # skip first 300 frames
        frame_skip = 300

        while True:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LCTRL:
                            drone.takeoff()
                        if event.key == pygame.K_w:
                            drone.land()

                start_time = time.time()

                img = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                if SAVE_VIDEO:
                    out.write(img)
                resized_image = cv2.resize(img, (width, height))

                img2, x, y, w, h = handTracking.trackHandCPM(resized_image)
                if not handTracking.tracker.loss_track:
                    centerX, centerY = computer_center_points(x, y, w, h, resized_image)
                    throttleValue = -centerY / (height / 2)
                    yawValue = centerX / (width / 2)
                    if w * h >= 0.01 * width * height:
                        pitchValue = -0.2
                    elif w * h < 0.008 * width * height:
                        pitchValue = 0.2
                else:
                    throttleValue = 0
                    yawValue = 0
                    pitchValue = 0

                drone.set_throttle(throttleValue)
                drone.set_yaw(yawValue)
                drone.set_pitch(pitchValue)

                show_image(resized_image)
                frame_skip = int((time.time() - start_time) / frame.time_base)



    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
