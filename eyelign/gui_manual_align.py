import logging
import cv2
import os
import click
import json
import shutil
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, readable=True),
    envvar="EYELIGN_INPUT_DIR",
)

def cli(
    input_dir
):
    logging.info('Click left eye and right eye in order\n \
                If click wrong, press ESC to exit and align agin \
                    Aligned image info would not lost')
    read_json_path=os.path.join(input_dir,'.eyelign')
    align_file=json.load(open(read_json_path,'r'))
    
    # mouse callback helper function
    feature_points_2d = []
    FEATURE_NUM = 2
    def draw_circle(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            logging.info('Left eye aligned, now click right eye')
            cv2.circle(img,(x,y),10,(0,0,255),-1)
            feature_points_2d.append([x, y])
    
    exit_flag=False
    for file_name in align_file:
        ## Check if the eyes are detected
        data=align_file[file_name]
        lx=data['lx']
        if lx is None:
            logging.info(f'Manual align file {file_name}')
            img_path=os.path.join(input_dir,file_name)
            img = cv2.imread(img_path)
            cv2.namedWindow("image")
            cv2.setMouseCallback("image", draw_circle)
            while True:
                cv2.imshow("image", img)
                if len(feature_points_2d) == FEATURE_NUM:
                    if len(feature_points_2d)==2:
                        align_file[file_name]['lx']=feature_points_2d[0][0]
                        align_file[file_name]['ly']=feature_points_2d[0][1]
                        align_file[file_name]['rx']=feature_points_2d[1][0]
                        align_file[file_name]['ry']=feature_points_2d[1][1]
                    feature_points_2d = [] # reset
                    break
                if (cv2.waitKey(20) & 0xFF == 27):
                    exit_flag=True
                    break
        if exit_flag is True:
            break
    backup_path=os.path.join(input_dir,'.eyelign.bak')
    shutil.copy(read_json_path,backup_path)
    logging.info(f'Backup the original align file to {backup_path}')
    with open(read_json_path, 'w') as outfile:
        json.dump(align_file, outfile,indent=2)


if __name__ == "__main__":
    cli()
