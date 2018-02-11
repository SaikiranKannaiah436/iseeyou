## Dataset preparation

1. Extract the coco dataset, since the annotations are not in pascal voc 
format the datagenerator would only labels in voc format. Therefore the 
annotations must be converted to voc format.
`python datautils.py create_annotations name_of_annot_file destination`

1. Once the annotations are converted to voc format to make sure number 
of images are equal to number of annot files
`python datautils.py delete_diff img_path annot_path` 
