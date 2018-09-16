from moviepy.editor import VideoFileClip, concatenate_videoclips
from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.stats_manager import StatsManager
from scenedetect.detectors.content_detector import ContentDetector
import random
import os

framerate = 25


def find_scenes(video_path):
    # type: (str) -> List[Tuple[FrameTimecode, FrameTimecode]]
    video_manager = VideoManager([video_path])
    stats_manager = StatsManager()
    # Construct our SceneManager and pass it our StatsManager.
    scene_manager = SceneManager(stats_manager)

    # Add ContentDetector algorithm (each detector's constructor
    # takes detector options, e.g. threshold).
    scene_manager.add_detector(ContentDetector(threshold=30.0, min_scene_len=15))
    base_timecode = video_manager.get_base_timecode()

    # We save our stats file to {VIDEO_PATH}.stats.csv.
    stats_file_path = '%s.stats.csv' % video_path

    try:
        # If stats file exists, load it.
        if os.path.exists(stats_file_path):
            # Read stats from CSV file opened in read mode:
            with open(stats_file_path, 'r') as stats_file:
                stats_manager.load_from_csv(stats_file, base_timecode)

        # Set downscale factor to improve processing speed.
        video_manager.set_downscale_factor()

        # Start video_manager.
        video_manager.start()

        # Perform scene detection on video_manager.
        scene_manager.detect_scenes(frame_source=video_manager)

        # Obtain list of detected scenes.
        scene_list = scene_manager.get_scene_list(base_timecode)
        # Each scene is a tuple of (start, end) FrameTimecodes.

        print('List of scenes obtained:')
        for i, scene in enumerate(scene_list):
            print(
                'Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
                    i + 1,
                    scene[0].get_timecode(), scene[0].get_frames(),
                    scene[1].get_timecode(), scene[1].get_frames(),))

        # We only write to the stats file if a save is required:
        if stats_manager.is_save_required():
            with open(stats_file_path, 'w') as stats_file:
                stats_manager.save_to_csv(stats_file, base_timecode)

    finally:
        video_manager.release()

    return scene_list


def get_random_scene(scene_list):
    rand = random.randint(1, len(scene_list) - 1)
    return scene_list[rand]


def timecode_to_seconds(timecode):
    a = timecode.split(':')
    r = 0
    if len(a) == 3:
        h = int(float(a[0]))
        m = int(float(a[1]))
        s = int(float(a[2]))
        r = r + (h*3600)
        r = r + (m*60)
        r = r + s
    elif len(a) == 2:
        m = int(float(a[0]))
        s = int(float(a[1]))
        r = r + (m*60)
        r = r + s
    elif len(a) == 1:
        s = int(float(a[0]))
        r = s
    else:
        r = 0

    return r


def is_scene_valid(scene, clip_length):
    t1 = timecode_to_seconds(scene[1].get_timecode())
    t0 = timecode_to_seconds(scene[0].get_timecode())
    
    return (t1 - t0) > (clip_length + 1)


def frames_to_timecode(frames):
    return '{0:02d}:{1:02d}:{2:02d}.{3:02d}'.format(int(frames / (3600*framerate)),
                                                    int(frames / (60*framerate) % 60),
                                                    int(frames / framerate % 60),
                                                    int(frames % framerate))


def generate_video(scene_list, source_path):
    clips = []
    length = 120
    bpm = 100
    clip_length = bpm / 60
    x_range = round(length / clip_length)
    used_scenes = []

    for x in range(0, x_range):
        random_scene = get_random_scene(scene_list)
        print('Fetch random scene timecode %s' % (random_scene[0].get_timecode()))

        while is_scene_valid(random_scene, clip_length) is False and random_scene not in used_scenes:
            random_scene = get_random_scene(scene_list)
            print('Invalid random scene, new random scene timecode:  %s' % (random_scene[0].get_timecode()))

        used_scenes.append(random_scene)

        start_frames = random_scene[0].get_frames() + 25
        end_frames = start_frames + 35

        start_timecode = frames_to_timecode(start_frames)
        end_timecode = frames_to_timecode(end_frames)

        print('Start: %s / End %s' % (start_timecode, end_timecode))

        clip = VideoFileClip(source_path).subclip(start_timecode, end_timecode)
        clips.append(clip)

    print('Concatenating clips ...')
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile('dist/my_concatenation.mp4')


def main():
    source_path = 'source/source.cut.25.mp4'

    scene_list = find_scenes(source_path)
    generate_video(scene_list, source_path)


if __name__ == "__main__":
    main()
