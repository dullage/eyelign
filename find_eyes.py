import cv2

MIN_FACE_SIZE = (100, 100)

face_cascade = cv2.CascadeClassifier(
    "./classifiers/haarcascade_frontalface_default.xml"
)
landmark_detector = cv2.face.createFacemarkLBF()
landmark_detector.loadModel("./models/lbfmodel.yaml")


def load_image(image_path, gray_only=True):
    img = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if gray_only:
        return img_gray
    else:
        return img, img_gray


def get_faces(img_gray):
    faces = face_cascade.detectMultiScale(
        img_gray, 1.1, 5, minSize=MIN_FACE_SIZE
    )
    if len(faces) != 1:
        raise Exception("No face or too much face!")
    return faces


def get_landmarks(img_gray, faces):
    _, landmarks = landmark_detector.fit(img_gray, faces)
    return landmarks


def find_eyes(image_path):
    img_gray = load_image(image_path)
    faces = get_faces(img_gray)
    landmarks = get_landmarks(img_gray, faces)
    left_eye = landmarks[0][0][36]
    right_eye = landmarks[0][0][45]
    return (
        (int(left_eye[0]), int(left_eye[1])),
        (int(right_eye[0]), int(right_eye[1])),
    )


def show(faces, landmarks, img):
    for x, y, w, h in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0), 2)
    for landmark in landmarks:
        for x, y in landmark[0]:
            cv2.circle(img, (x, y), 1, (255, 255, 255), 1)
    cv2.imshow("Preview", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    img, img_gray = load_image("./input/test-image2.jpg")
    faces = get_faces(img_gray)
    landmarks = get_landmarks(img_gray, faces)
    show(faces, landmarks, img)
