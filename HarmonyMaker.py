import cv2
import numpy as np
from cv2 import VideoWriter, VideoWriter_fourcc

class HarmonyMakerPart:
    def __init__(self, my_progression, my_BPM):
        self.progression = my_progression
        self.BPM = my_BPM

        # Progression is an array of arrays (matrix) of tuplet arrays, where
        # first item determines the number of beats per measure and the second
        # item is the featured text

class HarmonyMaker:
    def __init__(self, my_width, my_height, my_FPS):
        self.width = my_width
        self.height = my_height
        self.FPS = my_FPS

        self.parts = []
        self.part_ordering = []

        #Initialize video luggage
        fourcc = VideoWriter_fourcc(*'MP42')
        self.video = VideoWriter('./HarmonyMakerOutput.avi', fourcc, float(self.FPS), (self.width, self.height))

        self.font = cv2.FONT_HERSHEY_SIMPLEX #base size 22 or 10
    def LoadParts(self, source_path):
        try:
            dataFile = open(source_path, "r")
            rawLines = dataFile.readlines()

            header_line = rawLines[0].split(" ")
            number_of_parts = int(header_line[0])
            beats_in_count_off = int(header_line[1])
            is_count_off_BPM_determined = False
            count_off_BPM = 0

            index = 1

            self.parts = []
            for i in range(number_of_parts):
                cur_header = rawLines[index].split(" ")
                number_of_part_lines = int(cur_header[0])
                cur_part_BPM = int(cur_header[1])
                if is_count_off_BPM_determined == False:
                    is_count_off_BPM_determined = True
                    count_off_BPM = cur_part_BPM
                    self.parts.append(HarmonyMakerPart([[[beats_in_count_off, "..."],[beats_in_count_off, "..."]]], count_off_BPM))
                cur_part_progression = []
                for j in range(index + 1, index + number_of_part_lines + 1):
                    cur_progression_line = rawLines[j].split(" ")
                    cur_part_progression.append([])
                    for k in range(0,len(cur_progression_line),2):
                        if k == len(cur_progression_line) - 2:
                            #last item, trim off the newline char
                            cur_part_progression[-1].append([int(cur_progression_line[k]),cur_progression_line[k+1][:-1]])
                        else:
                            cur_part_progression[-1].append([int(cur_progression_line[k]),cur_progression_line[k+1]])
                index = index + number_of_part_lines + 1
                self.parts.append(HarmonyMakerPart(cur_part_progression, cur_part_BPM))
            raw_part_ordering = rawLines[index].split(" ")
            self.part_ordering = [[0,1]]
            for i in range(0,len(raw_part_ordering),2):
                self.part_ordering.append([int(raw_part_ordering[i]), int(raw_part_ordering[i+1])])

            #for rawLine in rawLines:
            #    splitLine = rawLine.split(" ")
            #    names.append(splitLine[0])
            #    sortedData.append(splitLine[1].split())
            dataFile.close()
            #return sortedData, names
        except FileNotFoundError:
            print("Shoggoth ate your file")
            return(0)
    def PrintParts(self):
        for i in range(len(self.parts)):
            print("Part " + str(i) + " in " + str(self.parts[i].BPM) + " BPM:")
            for j in self.parts[i].progression:
                cur_line = ""
                for k in j:#self.parts[i].progression[j]:
                    cur_line += "(" + str(k[0]) + " beats of " + k[1] + ")"
                print(cur_line)
        print("Part ordering:")
        for i in self.part_ordering:
            print("  Part " + str(i[0]) + " will play " + str(i[1]) + " times.")
    #Video methods
    def ReleaseVideo(self):
        self.video.release()
    def VisualizePart(self, part_index, repetitions, next_part_index):
        #frames_in_n_beats = N * 60.0 / BPM * FPS
        #Set next_part_index to -1 to indicate the last part
        cur_progression = self.parts[part_index].progression
        if next_part_index != -1:
            next_progression = self.parts[next_part_index].progression
        cur_BPM = self.parts[part_index].BPM
        #Create frames
        frames = []

        max_boxes_in_line = 0
        total_beats = 0
        beat_offsets = [[0]] #Assign to each measure after how many beats from the beginning it starts
        for chord_line in cur_progression:
            if len(chord_line) > max_boxes_in_line:
                max_boxes_in_line = len(chord_line)
            for item_i in range(len(chord_line)):
                total_beats += chord_line[item_i][0]
                if item_i == len(chord_line) - 1:
                    beat_offsets.append([beat_offsets[-1][-1]+chord_line[item_i][0]])
                else:
                    beat_offsets[-1].append(beat_offsets[-1][-1]+chord_line[item_i][0])
        cur_total_frames = round(total_beats * 60 * self.FPS / cur_BPM)
        print("Number of frames " + str(cur_total_frames))
        for i in range(cur_total_frames):
            frames.append(np.zeros((self.height,self.width,3), dtype=np.uint8))

        for i in range(cur_total_frames):
            frames[i] = cv2.rectangle(frames[i],(0,0),(self.width,self.height),(255,255,255),-1)

        #Draw the boxes
        box_width = 200
        box_height = 100
        box_offset_x = (self.width) / 2 - max_boxes_in_line * box_width / 2
        box_offset_y = 120 + (self.height - 120 - 120) / 2 - len(cur_progression) * box_height / 2

        metronome_box_width = 110
        metronome_box_height = 30
        metronome_offset_x = 300 + (self.width - 300 - 300) / 2
        metronome_offset_y = (120 - metronome_box_height) / 2

        for i in range(cur_total_frames):
            #Determine which box should be highlighted
            highlighted_y = -1
            highlighted_x = -1
            item_starting_frame = -1
            item_ending_frame = -1
            if i != 0:
                for y in range(len(beat_offsets)-1):
                    for x in range(len(beat_offsets[y])):
                        cur_beat_offset = beat_offsets[y][x]
                        if x == len(beat_offsets[y])-1:
                            next_beat_offset = beat_offsets[y+1][0]
                        else:
                            next_beat_offset = beat_offsets[y][x+1]
                        if i > cur_beat_offset * 60.0 / cur_BPM * self.FPS and i <= next_beat_offset * 60.0 / cur_BPM * self.FPS:
                            highlighted_x = x
                            highlighted_y = y
                            item_starting_frame = cur_beat_offset * 60.0 / cur_BPM * self.FPS
                            item_ending_frame = next_beat_offset * 60.0 / cur_BPM * self.FPS
                            cur_frame_span = item_ending_frame - item_starting_frame
                            frames_in_beat = cur_frame_span / cur_progression[y][x][0]
                            cur_beat = int(np.ceil((i - item_starting_frame) / frames_in_beat))
                            break
                    if highlighted_x != -1:
                        break
            else:
                highlighted_x = 0
                highlighted_y = 0
                item_starting_frame = 0
                if len(beat_offsets[0]) > 1:
                    item_ending_frame = beat_offsets[0][1] * 60.0 / cur_BPM * self.FPS
                else:
                    item_ending_frame = beat_offsets[1][0] * 60.0 / cur_BPM * self.FPS
                cur_frame_span = item_ending_frame - item_starting_frame
                frames_in_beat = cur_frame_span / cur_progression[0][0][0]
                cur_beat = 1
            #Draw the progression
            for y in range(len(cur_progression)):
                for x in range(len(cur_progression[y])):
                    cur_text_size = cv2.getTextSize(text=cur_progression[y][x][1], fontFace=self.font, fontScale=1, thickness=cv2.LINE_AA)
                    cur_text_width = cur_text_size[0][0]
                    cur_text_height = cur_text_size[1]

                    if y == highlighted_y and x == highlighted_x:
                        frames[i] = cv2.rectangle(frames[i],(round(box_offset_x + x * box_width), round(box_offset_y + y * box_height)),(round(box_offset_x + (x + 1) * box_width), round(box_offset_y + (y + 1) * box_height)),(220,230,230),-1)
                        #Draw the metronome
                        if cur_progression[y][x][0] * metronome_box_width > (self.width - 606):
                            cur_metronome_offset_x = 303
                            cur_metronome_box_width = np.floor((self.width - 606) / cur_progression[y][x][0])
                        else:
                            cur_metronome_box_width = metronome_box_width
                            cur_metronome_offset_x = metronome_offset_x - cur_progression[y][x][0] * metronome_box_width / 2

                        metronome_text_size = cv2.getTextSize(text=str(cur_beat) + "/" + str(cur_progression[y][x][0]), fontFace=self.font, fontScale=2, thickness=cv2.LINE_AA)
                        frames[i] = cv2.putText(frames[i],str(cur_beat) + "/" + str(cur_progression[y][x][0]),(round(self.width - 300 / 2 - metronome_text_size[0][0] / 2), round(120 / 2 + metronome_text_size[1] / 2)), self.font, 2,(0,0,0),2,cv2.LINE_AA)
                        frames[i] = cv2.rectangle(frames[i],(round(cur_metronome_offset_x), round(metronome_offset_y)),(int(round(cur_metronome_offset_x + (i - item_starting_frame) * cur_metronome_box_width * cur_progression[y][x][0] / cur_frame_span)), int(round(metronome_offset_y + metronome_box_height))),(150,240,150),-1)
                        for m_i in range(cur_beat - 1):
                            frames[i] = cv2.rectangle(frames[i],(int(round(cur_metronome_offset_x + m_i * cur_metronome_box_width)), int(round(metronome_offset_y))),(int(round(cur_metronome_offset_x + (m_i+1) * cur_metronome_box_width)), int(round(metronome_offset_y + metronome_box_height))),(100,220,100),-1)
                        for m_i in range(cur_progression[y][x][0]):
                            frames[i] = cv2.rectangle(frames[i],(int(round(cur_metronome_offset_x + m_i * cur_metronome_box_width)), int(round(metronome_offset_y))),(int(round(cur_metronome_offset_x + (m_i+1) * cur_metronome_box_width)), int(round(metronome_offset_y + metronome_box_height))),(0,0,0),2)

                    frames[i] = cv2.rectangle(frames[i],(round(box_offset_x + x * box_width), round(box_offset_y + y * box_height)),(round(box_offset_x + (x + 1) * box_width), round(box_offset_y + (y + 1) * box_height)),(0,0,0),3)
                    frames[i] = cv2.putText(frames[i],cur_progression[y][x][1],(round(box_offset_x + x * box_width + box_width / 2 - cur_text_width / 2), round(box_offset_y + y * box_height + box_height / 2 + cur_text_height / 2)), self.font, 1,(0,0,0),2,cv2.LINE_AA)
            #Draw next progression
            if next_part_index != -1:
                next_box_offset_x = 470
                next_box_offset_y = self.height - 120 / 2 - box_height / 2

                next_up_text_size = cv2.getTextSize(text="Next up: ", fontFace=self.font, fontScale=2, thickness=cv2.LINE_AA)
                frames[i] = cv2.putText(frames[i],"Next up: ",(round(next_box_offset_x / 2 - next_up_text_size[0][0] / 2), round(self.height - 120 / 2 + next_up_text_size[1] / 2)), self.font, 2,(0,0,0),2,cv2.LINE_AA)
                if len(next_progression[0]) > 4:
                    max_next_x = 4
                else:
                    max_next_x = len(next_progression[0])
                for x in range(max_next_x):
                    next_text_size = cv2.getTextSize(text=next_progression[0][x][1], fontFace=self.font, fontScale=1, thickness=cv2.LINE_AA)
                    next_text_width = next_text_size[0][0]
                    next_text_height = next_text_size[1]
                    frames[i] = cv2.rectangle(frames[i],(round(next_box_offset_x + x * box_width), round(next_box_offset_y)),(round(next_box_offset_x + (x + 1) * box_width), round(next_box_offset_y + box_height)),(0,0,0),3)
                    frames[i] = cv2.putText(frames[i],next_progression[0][x][1],(round(next_box_offset_x + x * box_width + box_width / 2 - next_text_width / 2), round(next_box_offset_y + box_height / 2 + next_text_height / 2)), self.font, 1,(0,0,0),2,cv2.LINE_AA)
            else:
                next_up_text_size = cv2.getTextSize(text="This is the last part", fontFace=self.font, fontScale=2, thickness=cv2.LINE_AA)
                frames[i] = cv2.putText(frames[i],"This is the last part",(round(self.width / 2 - next_up_text_size[0][0] / 2), round(self.height - 120 / 2 + next_up_text_size[1] / 2)), self.font, 2,(0,0,0),2,cv2.LINE_AA)
        #Draw the frames
        for loop_index in range(repetitions):
            for i in range(cur_total_frames):
                cur_frame = frames[i].copy()
                cur_loop_count_text_size = cv2.getTextSize(text=str(loop_index+1)+"/"+str(repetitions), fontFace=self.font, fontScale=3, thickness=cv2.LINE_AA)
                cur_frame  = cv2.putText(cur_frame,str(loop_index+1)+"/"+str(repetitions),(round(150 - cur_loop_count_text_size[0][0]/2),round(60 + cur_loop_count_text_size[1])), self.font, 3,(0,0,0),2,cv2.LINE_AA)
                self.video.write(cur_frame)
    def MakeVideo(self):
        for i in range(len(self.part_ordering)-1):
            self.VisualizePart(self.part_ordering[i][0],self.part_ordering[i][1],self.part_ordering[i+1][0])
        self.VisualizePart(self.part_ordering[-1][0],self.part_ordering[-1][1],-1)


lmao = HarmonyMaker(1280, 720, 24)
lmao.LoadParts("test_piece.txt")
lmao.PrintParts()
#lmao.VisualizePart(2,2,1)
lmao.MakeVideo()
lmao.ReleaseVideo()
#seconds = 10

#for _ in range(FPS*seconds):
#    frame = np.random.randint(0, 256,
#                              (height, width, 3),
#                              dtype=np.uint8)
#    video.write(frame)

#video.release()
