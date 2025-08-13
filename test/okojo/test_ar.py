from okojo.ar import ArchiveObject
import os

def main():
    curdir = os.path.dirname(os.path.abspath(__file__))
    arpath = os.path.join(curdir, "ar", "archive.a")
    archive = ArchiveObject(arpath)
    archive.read_all()


if __name__ == "__main__":
    main()
