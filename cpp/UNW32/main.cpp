#include <arpa/inet.h>
#include <fcntl.h>
#include <iostream>
#include <netdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <termios.h>
#include <unistd.h>
#include <opencv2/opencv.hpp>
#include <opencv/cv.h>
#include <bitset>
#include <ctime>

using namespace std;
using namespace cv;


int send(uint32_t message[7],int sfd, fd_set wfd,struct timeval to)
{
    int n = sfd + 1;
    int com;
    int bytes_sent;
    com = select(n, NULL, &wfd , NULL , &to);
    if(com == 0)
    {
        //cout<<"timeout\n";
        return -1;
    }
    else if(com > 0)
    {
        for(int serialize = 0; serialize < 7; serialize++)
        {

            bytes_sent = send(sfd, &message[serialize], 1, 0);
            //cout << hex << message[serialize] << "\n";
        }
        //cout << message[4] << "\n";
        //cout <<"sent \n";
        return bytes_sent;
    }
    else if (com == -1)
        //cout<< "error\n";
    return -1;
}

int receive(int sfd, fd_set rfd,struct timeval to)
{
    uint8_t buffer[16];

    uint8_t *num, *d;
    uint8_t byte;
    unsigned int out;
    int n = sfd + 1, enable = 0, com, start = 0, msgPos, chksum;
    com = select(n, &rfd, NULL, NULL, &to);
    if(com == 0)
    {
        //cout << "timeout recv \n";
        return -1;
    }
    else if(com > 0)
    {
        //cout << "recieve\n";
        recv(sfd, buffer, 12, 0);
        num = buffer;
        start = 0;
        for(int x = 0; x< 16; x++)
        {

            d = num + x;
            byte = *d;
            out = byte;
            if(byte == 0x88)
            {
                if(x>4){
                    memset(&buffer, 0, sizeof buffer);
                    return -1;
                }
                start = 1;
                msgPos = 0;
                //cout << "start\n";
            }
            if(start ==1)
            {
                if(msgPos == 1 && byte != 0x01)
                {
                    //cout << byte;

                }
                /*if(msgPos == 4 || msgPos == 5)
                {
                    cout <<"IR:\t" << hex << out << "\n";
                }*/
                if(msgPos == 6)
                {
                    cout <<"UV:\t" << hex << out << "\n";
                    enable = byte;
                }
                /*if(msgPos == 7)
                {
                    bitset<8> bin(out);
                    cout <<"Con:\t" << bin <<"\n";
                }
                if(msgPos == 8)
                {
                    bitset<8> bin(out);
                    cout <<"Active:\t" << bin <<"\n";
                }
                if(msgPos == 10)
                {

                }*/
                if(out == 0xd)
                {
                    //cout<< "end\n";
                    memset(&buffer, 0, sizeof buffer);
                    return enable;
                }
                chksum++;
                msgPos++;
           }

        }
        memset(&buffer, 0, sizeof buffer);
        return -1;
    }
    cout<<"error\n";
    memset(&buffer, 0, sizeof buffer);
    return -2;
}

int main(int argc, char *argv[])
{
    int LVal = 0;
    int table[25] = {   160,    144,    192,    136,    132,
                        96,     80,     130,    72,     68,
                        48,     40,     66,     20,     12,
                        34,     18,     65,     10,     6,
                        33,     17,      3,      9,     5};


    int con=1, status = 1, sockfd, sockfd2,counter = 0, yUp,yLow, xUp, xLow;
    struct addrinfo hints, *res;
    struct addrinfo hints2, *res2;
    fd_set readfd, writefd;
    struct timeval timeout;
    uint8_t init = 0xB3, address = 0x01, bytes = 0x07, pad = 0x10, payload = 0x00, chksum = 0x05, term = 0x0D;
    payload = 0x00;
    uint32_t msg[7] = {init, address, bytes, pad, payload, chksum, term};

    memset(&hints, 0, sizeof hints);
    memset(&hints2, 0, sizeof hints2); // make sure the struct is empty
    hints.ai_family = AF_UNSPEC;     // don't care IPv4 or IPv6
    hints.ai_socktype = SOCK_STREAM; // TCP stream sockets
    hints2.ai_family = AF_UNSPEC;     // don't care IPv4 or IPv6
    hints2.ai_socktype = SOCK_DGRAM; // TCP stream sockets

    while (status != 0)
        status = getaddrinfo("169.254.202.181", "10001", &hints, &res);
    sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    cout << "sockfd\n";
    while (con != 0)
        con = connect(sockfd, res->ai_addr, res->ai_addrlen);
    cout << "con\n";
    status = 1;
    con = 1;
    while (status != 0)
        status = getaddrinfo("169.254.158.235", "10002", &hints2, &res2);
    sockfd2 = socket(res2->ai_family, res2->ai_socktype, res2->ai_protocol);
    cout << "sockfd\n";
    bind(sockfd2, res2->ai_addr, res2->ai_addrlen);
    listen(sockfd2,5);
    cout << "con\n";
    fcntl(sockfd, F_SETFL, O_NONBLOCK);
    fcntl(sockfd2, F_SETFL, O_NONBLOCK);
    FD_ZERO(&readfd);
    FD_ZERO(&writefd);
    FD_SET(sockfd2, &readfd);
    FD_SET(sockfd, &writefd);
    timeout.tv_usec = 30000;
    int fireLoc[2];
    Mat frame, base, change, tmp0, tmp1, tmp2, tmp3, tmp4;
    double low, high;

    //bytes_sent = send(sockfd, msg, 8, 0);
    //cout << bytes_sent << "\n";
    //pid_t pid = fork();

    //if (pid == 0){
    int enable = 0;

    base = imread("C:/UNW32/frame.bmp",0);
    imwrite("base.bmp",base);
    tmp0 = base;
    tmp1 = base;
    tmp2 = base;
    tmp3 = base;
    tmp4 = base;

    Size s = base.size();
    int rows = s.width;
    int cols = s.height;
    int xsect = 54, ysect = 54;
    //int xsect = ceil((rows)/5), ysect = ceil((cols)/5);
    cout << xsect<< "\t" << ysect<<"\n";
    //namedWindow("Continuous Update", WINDOW_AUTOSIZE);
    //namedWindow("Base",WINDOW_AUTOSIZE);
    while(1){
        do
        {
            try{
                frame = imread("C:/UNW32/frame.bmp",0);
            } catch(...){}
        } while(frame.empty());

        //base.release();

        //base = imread("C:/UNW32/base.bmp",0);

        //change = frame - base;
        //minMaxLoc(base, NULL, &low, NULL, NULL);
        minMaxLoc(frame, NULL, &high, NULL, NULL);
        //cout << high << "high  Low" << low << "\n";
        if(high >= 1)
        {
                cout<<high<<"\n";
                for(int xPixel = 415; xPixel > 143; xPixel--){
                    for(int yPixel = 315; yPixel > 43; yPixel--){
                         if(frame.at<uchar>(yPixel,xPixel) >= high){

                            if(yPixel > yUp)
                                yUp = yPixel;
                            if(yPixel < yLow)
                                yLow = yPixel;
                            if(xPixel > xUp)
                                xUp = xPixel;
                            /*if(xPixel < xLow)
                                xLow = xPixel;*/
                         }
                    }
                }
                fireLoc[0] = (yUp + yLow)/2; fireLoc[1] = xUp;
                cout << dec << xLow << "\t" << xUp << "\n" << yLow << "\t" << yUp << "\n";
                xUp = 0; xLow =415; yUp = 0; yLow = 315;

                imwrite("change.bmp",frame);
                cout << "FIRE X: " << fireLoc[1] << "\t" << floor((fireLoc[1]-140)/xsect) << "\nY: " << fireLoc[0] << "\t" << floor((fireLoc[0]-90)/ysect) << "\n";
                LVal = 5*(floor((fireLoc[0]-40)/ysect)) + (floor((fireLoc[1]-140)/xsect));
                payload = table[LVal];
                msg[4] = payload;
                bitset<8> bin(msg[4]);
                cout << bin << "\n";

                for(int loop = 0; loop<50; loop++){
                    send(msg,sockfd,writefd,timeout);
                    enable = receive(sockfd2 ,readfd, timeout);
                    if(enable == 0){
                        break;
                    }
                }
                msg[4] = 0;

                 for(int loop = 0; loop<100; loop++){
                    send(msg,sockfd,writefd,timeout);
                }
/*
                tmp0 = base;
                tmp1 = base;
                tmp2 = base;
                tmp3 = base;
                tmp4 = base;*/
            }
/*
            if(counter == 0)
            {
                imwrite("C:/UNW32/base.bmp",tmp1);
                tmp0 = frame;
                //cout << "base change1\n";
                counter ++;
            }
            else if(counter == 1)
            {
                imwrite("C:/UNW32/base.bmp",tmp2);
                tmp1 = frame;
                //cout << "base change2\n";
                counter++;
            }
            else if(counter == 2)
            {
                imwrite("C:/UNW32/base.bmp",tmp3);
                tmp2 = frame;
                //cout << "base change3\n";
                counter++;
            }
            else if(counter == 3)
            {
                imwrite("C:/UNW32/base.bmp",tmp4);
                tmp3 = frame;
                //cout << "base change4\n";
                counter = 4;
            }
            else if(counter == 4)
            {
                imwrite("C:/UNW32/base.bmp",tmp0);
                tmp4 = frame;
                //cout << "base change4\n";
                counter = 0;
            }
            //else gettimeofday(&startTV, NULL);
*/        }


    close(sockfd);
    freeaddrinfo(res); // free the linked-list
}
