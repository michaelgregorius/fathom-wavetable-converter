# Wavetable converter for the Fathom synthesizer

This script converts wave files into the wavetable format of the Fathom synthesizer. The files to be converted have to meet the following conditions:
* The file contains wav data and its extension is "wav".
* The file is mono and is in 16 or 32 bit PCM format. So files in IEEE float format will *not* work!

The script takes the following parameters:
```
  -f, --file: Convert the single file "filename".
  -d, --dir: Recursively convert all files in the given directory.
  -g, --targetdir: Put all converted files into the given target directory. If
                   this parameter is not given and you convert a whole
                   directory then all files will be put next to the original
                   files.
  -l, --length: The number of samples in one cycle that's assumed for wave table files.
  -w: Mode that converts Fathom XML to wav files. Provide the file to convert
      using the -f option. The resulting file will have the same name as the
      input file with ".wav" appended.

Parameters for meta data:
  -c, --category: Use the given category for all converted files
  -a, --author: Use the given author for all converted files
  -m, --comment: Use the given comment for all converted files
  -r, --rating: Use the given rating (in [0, 10]) for all converted files
  -t, --type: Use the given type for all converted files
```

## Examples
Convert a wavetable file. Because the -t parameter is not used one cycle is assumed to be 2048 samples long.
```
FathomWTCreator.py -f Input.wav
```
Convert a wavetable file that contains cycles of length 1024 (example for some long arguments):
```
FathomWTCreator.py --file=Input.wav --length=1024
```
Convert everything in directory "source" and write the converted files into the directory "converted":
```
FathomWTCreator.py -d source -g converted
```
Convert everything in directory "source" and write the converted files next to the original files:
```
FathomWTCreator.py -d source
```
Example usage for the meta data:
```
FathomWTCreator.py -f "Input.wav" -c "A category" -a "Joe Doe" -m "A comment" -r 10
```
Example usage to convert the file "Input.xml" to "Input.xml.wav":
```
FathomWTCreator.py -w -f "Input.xml"
```