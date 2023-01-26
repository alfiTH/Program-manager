#include <iostream>
#include <unistd.h>

int main(int argc, char const *argv[])
{
    std::cout <<"argv[0]" << std::endl;
    for(int i = 0; i < argc;i++)
        std::cout <<argv[i] << std::endl;
    std::cout << "holaaaa soy c"<<std::endl;
    for (int i = 0; i <1000;i++) {
        std::cout <<"k"<<i<<std::endl;
        sleep(0.001);
    }


    return 0;
}
