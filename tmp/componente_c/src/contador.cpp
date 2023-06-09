#include <iostream>
#include <unistd.h>

int main(int argc, char const *argv[])
{
    std::cout <<"argv[0]" << std::endl;
    for(int i = 0; i < argc;i++)
        std::cout <<argv[i] << std::endl;
    std::cout << "holaaaa soy c"<<std::endl;
    for (int i = 0; i <50;i++) {
        std::cout <<"k"<<i<<std::endl;
        std::cout.flush();
        sleep(1);
    }


    return 0;
}
