if not exist "cropped" (
    mkdir "cropped"
)

for %%i in (*.jpg) do ffmpeg -i "%%i" -vf "crop=in_w/3:in_h:in_w/3*2:0" "cropped\%%i" >nul 2>&1