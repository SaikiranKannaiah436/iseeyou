import baker
import json
from path import Path
import os
from cytoolz import merge, join, groupby
from cytoolz.compatibility import iteritems
from cytoolz.curried import update_in
from itertools import starmap
from collections import deque
from lxml import etree, objectify


def keyjoin(leftkey, leftseq, rightkey, rightseq):
    return starmap(merge, join(leftkey, leftseq, rightkey, rightseq))


def root(folder, filename, width, height):
    E = objectify.ElementMaker(annotate=False)
    return E.annotation(
            E.folder(folder),
            E.filename(filename),
            E.source(
                E.database('MS COCO'),
                E.annotation('MS COCO'),
                E.image('Flickr'),
                ),
            E.size(
                E.width(width),
                E.height(height),
                E.depth('3'),
                ),
            )


def instance_to_xml(anno):
    E = objectify.ElementMaker(annotate=False)
    xmin, ymin, width, height = anno['bbox']
    return E.object(
            E.name(anno['category_id']),
            E.bndbox(
                E.xmin(xmin),
                E.ymin(ymin),
                E.xmax(xmin+width),
                E.ymax(ymin+height),
                ),
            )


def get_instances(coco_annotation):
    coco_annotation = Path(coco_annotation).expand()
    content = json.loads(coco_annotation.text())
    print(content.keys())
    categories = {d['id']: d['name'] for d in content['categories']}
    return categories, tuple(keyjoin('id', content['images'], 
'image_id', content['annotations']))

def rename(name, year=2014):
        out_name = Path(name).stripext()
        # out_name = out_name.split('_')[-1]
        # out_name = '{}_{}'.format(year, out_name)
        return out_name


@baker.command
def create_imageset(coco_annotation, dst):
    _ , instances= get_instances(coco_annotation)
    dst = Path(dst).expand()

    for instance in instances:
        name = rename(instance['file_name'])
        dst.write_text('{}\n'.format(name), append=True)

@baker.command
def create_annotations(coco_annotation, dst):
    categories , instances= get_instances(coco_annotation)
    dst = Path(dst).expand()

    for i, instance in enumerate(instances):
        instances[i]['category_id'] = categories[instance['category_id']]

    for name, group in iteritems(groupby('file_name', instances)):
        out_name = rename(name)
        annotation = root('VOC2014', '{}.jpg'.format(out_name), 
                          group[0]['height'], group[0]['width'])
        for instance in group:
            annotation.append(instance_to_xml(instance))
        
        print(out_name)
        etree.ElementTree(annotation).write(dst/'{}.xml'.format(out_name))

@baker.command
def delete_diff(img_folder, annot_folder):
    num_to_del = len(os.listdir(img_folder)) - len(os.listdir(annot_folder))
    if num_to_del == 0:
        return('number of images equal to number of annotations')
    img_names_full = os.listdir(img_folder)
    annot_names_full = os.listdir(annot_folder)
    all_img_names = [each_file.split('.')[0] for each_file in img_names_full]
    all_annot_names = [each_file.split('.')[0] for each_file in annot_names_full]
    
    names_to_del = set(all_img_names) ^ set(all_annot_names)
    
    if num_to_del == len(names_to_del):
        
        os.makedirs('./removed_files')
        for each_name in names_to_del:
            if each_name in all_img_names:
                os.rename(os.path.join(img_folder, each_name+'.jpg'), os.path.join('./removed_files', each_name+'.jpg'))
            elif each_name in all_annot_names:
                os.rename(os.path.join(annot_folder, each_name+'.xml'), os.path.join('./removed_files', each_name+'.xml'))
            else:
                print('anomaly: ', each_name)




if __name__ == '__main__':
    baker.run()
