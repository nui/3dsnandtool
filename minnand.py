import os
import sys
from collections import namedtuple

import shutil

SECTOR_SIZE = 512

Part = namedtuple('Part', ['p1start', 'p1sectors', 'image', 'xorpad', 'mountpoint'])

n3ds = {
    'ctrnand': Part(p1start=343 * SECTOR_SIZE,
                    p1sectors=2156905,
                    image='ctrnand_full.bin',
                    xorpad='ctrnand_full.bin.xorpad',
                    mountpoint='ctrnand'),
    'twln': Part(p1start=0 * SECTOR_SIZE,
                 p1sectors=294313,
                 image='twln.bin',
                 xorpad='twln.bin.xorpad',
                 mountpoint='twln'),
}

o3ds = {
    'ctrnand': Part(p1start=357 * SECTOR_SIZE,
                    p1sectors=1548059,
                    image='ctrnand_full.bin',
                    xorpad='ctrnand_full.bin.xorpad',
                    mountpoint='ctrnand'),
    'twln': Part(p1start=0 * SECTOR_SIZE,
                 p1sectors=294313,
                 image='twln.bin',
                 xorpad='twln.bin.xorpad',
                 mountpoint='twln'),
}


def generate_blank_pattern():
    with open('unused_sector.bin', 'wb+') as f:
        f.write(open('/dev/urandom', 'rb').read(SECTOR_SIZE))


def read_unused_pattern():
    return open('unused_sector.bin', 'rb+').read(SECTOR_SIZE)


def count_unused_sectors(part):
    image = open(part.image, 'rb+')
    image.seek(part.p1start)
    blank_pattern = read_unused_pattern()

    blank_sectors = 0
    for i in range(0, part.p1sectors):
        data = image.read(SECTOR_SIZE)
        if data == blank_pattern:
            blank_sectors += 1
    image.close()
    return blank_sectors


def fill_fat(part):
    blank_sectors = count_unused_sectors(part)
    garbage_path = os.path.join(part.mountpoint, 'garbage')

    if blank_sectors == 0:
        blank_pattern = read_unused_pattern()
        with open('unused_sector.bin', 'wb+') as f:
            f.write(blank_pattern)
            f.close()
        with open(garbage_path, 'wb+') as f:
            disk_free = shutil.disk_usage(part.mountpoint).free
            for _ in range(disk_free // SECTOR_SIZE):
                f.write(blank_pattern)
            f.flush()
            os.fsync(f.fileno())
            f.close()
        os.remove(garbage_path)
    else:
        print('blank pattern is not unique')
        sys.exit(1)


def min_part(part):
    image = open(part.image, 'rb+')
    image.seek(part.p1start)

    xorpad = open(part.xorpad, 'rb+')
    xorpad.seek(part.p1start)

    blank_pattern = read_unused_pattern()
    total_unused_sectors = 0

    for i in range(0, part.p1sectors):
        data = image.read(SECTOR_SIZE)
        xor = xorpad.read(SECTOR_SIZE)
        if data == blank_pattern:
            image.seek(-SECTOR_SIZE, os.SEEK_CUR)
            image.write(xor)
            total_unused_sectors += 1
    image.close()
    xorpad.close()
    print('Total {} Free space = {} MB'.format(part.mountpoint, total_unused_sectors * SECTOR_SIZE / 1024 / 1024))


def count_zero_in_unlocated_sectors(part):
    image = open(part.image, 'rb+')
    xorpad = open(part.xorpad, 'rb+')

    total_zero_sectors = 0

    for i in range(0, part.p1start):
        data = image.read(SECTOR_SIZE)
        xor = xorpad.read(SECTOR_SIZE)
        if data == xor:
            total_zero_sectors += 1
    return total_zero_sectors


def main():
    model = o3ds
    for k in model.keys():
        part = model[k]
        fill_fat(part)
        min_part(part)


if __name__ == '__main__':
    # generate_blank_pattern()
    main()
    # print(count_unused_sectors(n3ds['ctrnand']))
