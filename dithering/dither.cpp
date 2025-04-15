#include "dither.h"
#include <omp.h>
#include <opencv2/opencv.hpp>
#include <vector>
#include <optional>
#include <map>
#include <random>
#include <list>
#include <algorithm>
#include <iostream>

namespace
{
    std::random_device rd;
    std::mt19937 g(rd());
}

namespace dither
{
    namespace palettes
    {
        const auto waveshare7color = std::list{
            dither::color_map[dither::color::Black],
            dither::color_map[dither::color::White],
            dither::color_map[dither::color::Green],
            dither::color_map[dither::color::Blue],
            dither::color_map[dither::color::Red],
            dither::color_map[dither::color::Yellow],
            dither::color_map[dither::color::Orange]
        };
    }

    double colorDistance(const cv::Vec3b& color1, const cv::Vec3b& color2, const cv::NormTypes norm)
    {
        // transform BGR to LAB
        cv::Mat lab1, lab2;
        cv::cvtColor(cv::Mat(1, 1, CV_8UC3, color1), lab1, cv::COLOR_BGR2Lab);
        cv::cvtColor(cv::Mat(1, 1, CV_8UC3, color2), lab2, cv::COLOR_BGR2Lab);
        // convert to 3 channel
        lab1.convertTo(lab1, CV_64F);
        lab2.convertTo(lab2, CV_64F);

        auto dist = lab1 - lab2;

        // calculate the distance
        return cv::norm(dist, norm);
    }

    cv::Vec3b pixel_closest_colour(std::vector<cv::Vec3b>& palette, const cv::Vec3b& old_pixel,
                                   const cv::NormTypes norm)
    {
        std::optional<cv::Vec3b> closest_colour = std::nullopt;
        auto min_distance = std::numeric_limits<double>::max();
        std::ranges::shuffle(palette, g);
        #pragma omp for
        for (const auto& color : palette)
        {
            if (const auto distance = colorDistance(old_pixel, color, norm); distance < min_distance)
            {
                min_distance = distance;
                closest_colour = color;
            }
        }
        return closest_colour.value_or(palette.front());
    }

    void apply_neighbour_diffusion(const method& diff_method,
                                   cv::Mat& image, const int y, const int x,
                                   const cv::Vec3b& quantization_error)
    {
        #pragma omp for
        for (auto [dx, dy, diffusion_coefficient] : diffusion_map[diff_method])
        {
            const auto xn = x + dx;
            const auto yn = y + dy;
            if ((0 <= xn && xn < image.cols) && (0 <= yn && yn < image.rows))
            {
                image.at<cv::Vec3b>(yn, xn) +=
                    quantization_error * diffusion_coefficient;
            }
        }
    }

    void ditherImage(const std::list<cv::Vec3b>& palette, cv::Mat& image,
                     const method diff_method = FLOYD_STEINBERG, const cv::NormTypes norm = cv::NORM_L2)
    {
        std::vector<cv::Vec3b> colors = {palette.begin(), palette.end()};

        
        std::cout << "Dithering image using " << diff_method << " method" << std::endl;

        #pragma omp for 
        for (auto y = 0; y < image.rows; y++)
        {
            auto* pixel = image.ptr<cv::Vec3b>(y);
            std::cout.precision(2);
            std::cout << "\rprogress: " << 1.0 * y / image.rows << "\t" << std::flush;

            // shuffle the pixels in the row
            for (auto x = 0; x < image.cols; x++)
            {
                auto new_pixel = pixel_closest_colour(colors, pixel[x], norm);
                auto quantization_error = pixel[x] - new_pixel;
                
                pixel[x] = new_pixel;
                apply_neighbour_diffusion(diff_method, image, y, x, quantization_error);
                    
            }
        }
        std::cout << "\rprogress: done\t\t" << std::endl;
        // color each pixel in the image white
        #pragma omp for
        for (auto y = 0; y < image.rows; y++)
        {
            auto* pix = image.ptr<cv::Vec3b>(y);
            
            for (auto x = 0; x < image.cols; x++)
            {
               pix[x] = pixel_closest_colour(colors, pix[x], norm);
            }
        }
    }
}


void generateDitheredImage(const std::string& image_path, const std::string& out_path)
{
    cv::Mat img = cv::imread(image_path, cv::IMREAD_COLOR);
    dither::ditherImage(dither::palettes::waveshare7color, img, dither::STEVENSON_ARCE, cv::NORM_L2);
    cv::imwrite(out_path, img);
}

int main(const int argc, char** argv)
{
    if (argc != 3)
    {
        std::cerr << "Usage: " << argv[0] <<
            " <input_image_path> <output_image_path>"
            <<
            std::endl;
        return 1;
    }
    const std::string image_path = argv[1];
    const std::string out_path = argv[2];
    generateDitheredImage(image_path, out_path);
}
