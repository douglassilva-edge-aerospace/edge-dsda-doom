# 1. Create build folder and change to this directory
```bash
mkdir -p build 
cd build
```
# 2. Install dependencies
sudo apt install -y libzip-dev pkg-config libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libfluidsynth-dev libportmidi-dev libmad0-dev libvorbis-dev 
sudo apt install -y libogg-dev libdumb1-dev libopusfile-dev libvorbisfile3
sudo apt install libzip-dev zipcmp zipmerge ziptool
sudo apt install fluidsynth libfluidsynth-dev
# 3. Build using cmake 
cmake ../prboom2 -DCMAKE_BUILD_TYPE=Release

# 4. Compile
make -j$(nproc)
