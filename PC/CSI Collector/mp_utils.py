from mediapipe import solutions

def get_mp_pose_proccessor():
    return solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def get_simplified_pose(img, mp_pose_proccessor, target="recording", skip_incomplete=False):
    lm = (mp_pose_proccessor.process(img)).pose_landmarks
    if (len(lm.landmark)==0):
        return None

    if (skip_incomplete==True):
        for node in lm.landmark:
            if (node.x<0 or node.x>1 or node.y<0 or node.y>1):
                return None

    nodes = []
    nodes.append(((lm.landmark[7].x+lm.landmark[8].x)/2, (lm.landmark[7].y+lm.landmark[8].y)/2, (lm.landmark[7].z+lm.landmark[8].z)/2))
    nodes.append(((lm.landmark[11].x+lm.landmark[12].x)/2, (lm.landmark[11].y+lm.landmark[12].y)/2, (lm.landmark[11].z+lm.landmark[12].z)/2))
    nodes.append((lm.landmark[13].x, lm.landmark[13].y, lm.landmark[13].z))
    nodes.append((lm.landmark[15].x, lm.landmark[15].y, lm.landmark[15].z))
    nodes.append((lm.landmark[14].x, lm.landmark[14].y, lm.landmark[14].z))
    nodes.append((lm.landmark[16].x, lm.landmark[16].y, lm.landmark[16].z))
    nodes.append(((lm.landmark[23].x+lm.landmark[24].x)/2, (lm.landmark[23].y+lm.landmark[24].y)/2, (lm.landmark[23].z+lm.landmark[24].z)/2))
    nodes.append((lm.landmark[25].x, lm.landmark[25].y, lm.landmark[25].z))
    nodes.append((lm.landmark[27].x, lm.landmark[27].y, lm.landmark[27].z))
    nodes.append((lm.landmark[26].x, lm.landmark[26].y, lm.landmark[26].z))
    nodes.append((lm.landmark[28].x, lm.landmark[28].y, lm.landmark[28].z))
    if (target=="recording"):
        return nodes

    elif (target=="ploting"):
        while (len(lm.landmark)>len(nodes)):
            lm.landmark.pop(-1)
        for i in range(len(nodes)):
            lm.landmark[i].x = nodes[i][0]
            lm.landmark[i].y = nodes[i][1]
            lm.landmark[i].z = nodes[i][2]
            lm.landmark[i].visibility = 0.999
        return lm

def get_simplified_pose_connections():
    return ((0, 1), (1, 2), (1, 4), (1, 6), (2, 3), (4, 5), (6, 7), (6, 9), (7, 8), (9, 10))