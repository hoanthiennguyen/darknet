### This is the introduction how to run SQLE in your computer
- Create a directory `testing-images`, download images from https://drive.google.com/drive/folders/1gfiCoGzP-17xe5wSQHol1GnZLJCEnbOM?usp=sharing and save them in here
- Create a directory `weights`, download weights from 
https://drive.google.com/drive/folders/1CFJTOIk1YxjfeGVuq9oyyeoefzC2YlgM?usp=sharing and save them in here
- In Linux:
    - Run `make`. This will build C code to create a library called `libdarknet.so` which is then used in python code.
    - Run `poetry run python darknet_images.py --weights=weights/example.weights --input=testing-images/example.png`, replace `example` with the file's name you want to use. Add option `--dont_show` to the command if you don't want to see the output image
    
