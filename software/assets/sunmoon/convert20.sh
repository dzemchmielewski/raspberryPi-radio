#!/bin/bash

conversion () {
  convert $1 -background white -alpha remove -alpha off  BMP3:out1.bmp   
  convert out1.bmp -filter triangle -resize 38x16  BMP3:out2.bmp
  convert out2.bmp -filter spline -unsharp 0x1  BMP3:out3.bmp
  convert out3.bmp -filter spline -unsharp 0x1  BMP3:out4.bmp
  convert out4.bmp -depth 4 -colorspace gray -colors 16 BMP3:out5.bmp
  convert out5.bmp -negate BMP3:$1"_converted"
  rm out1.bmp out2.bmp out3.bmp out4.bmp out5.bmp
}


conversion $1


