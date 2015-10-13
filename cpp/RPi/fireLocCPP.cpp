#include <stdio.h>
#include <opencv2/opencv.hpp>

using namespace cv;

void findFire(Mat data){
	Mat blur, thresh;
	double maxVal;
	Scalar meanVal;
	GaussianBlur(data, blur, Size(3,3), 2);
	meanVal = mean(blur);
	minMaxLoc(blur, NULL, &maxVal, NULL, NULL);
	threshold(blur, thresh, (meanVal[0] + maxVal)/2, 255, 0);
	imwrite("mask.bmp",thresh);
}

int main(int argc, char** argv){
	char* imgName = argv[1];
	int fireLoc[2];
	Mat data;
	data = imread(imgName,0);
	findFire(data);

	return 0;
}
