#include "dither.h"

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
        cv::cvtColor(cv::Mat(1, 1, CV_8UC3, color1), lab1, cv::COLOR_BGR2YUV);
        cv::cvtColor(cv::Mat(1, 1, CV_8UC3, color2), lab2, cv::COLOR_BGR2YUV);
        return cv::norm(lab1, lab2, norm);
    }

    cv::Vec3b pixel_closest_colour(std::vector<cv::Vec3b>& palette, const cv::Vec3b& old_pixel,
                                   const cv::NormTypes norm)
    {
        std::optional<cv::Vec3b> closest_colour = std::nullopt;
        auto min_distance = std::numeric_limits<double>::max();
        std::ranges::shuffle(palette, g);
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


    void ditherImage(const std::list<cv::Vec3b>& palette, cv::Mat& image,
                     const method method = FLOYD_STEINBERG, const cv::NormTypes norm = cv::NORM_L2)
    {
        std::vector<cv::Vec3b> colors = {palette.begin(), palette.end()};
        std::cout.precision(2);
        const auto& diff_map = dither::diffusion_map[method];
        std::cout << "Dithering image using " << method << " method" << std::endl;
        auto y = 0;
        for (auto* row = image.ptr<cv::Vec3b>(y); y < image.rows; row = image.ptr<cv::Vec3b>(++y))
        {
            std::cout << "\rprogress: " << 1.0 * y / image.rows << "\t" << std::flush;
            auto x = 0;
            auto* pixel = row;
            while (x < image.cols)
            {
                auto new_pixel = pixel_closest_colour(colors, *pixel, norm);
                auto quantization_error = *pixel - new_pixel;
                *pixel = new_pixel;
                for (auto [dx, dy, diffusion_coefficient] : diff_map)
                {
                    const auto xn = x + dx;
                    const auto yn = y + dy;
                    if ((0 <= xn && xn < image.cols) && (0 <= yn && yn < image.rows))
                    {
                        image.at<cv::Vec3b>(yn, xn) +=
                            quantization_error * diffusion_coefficient;
                    }
                }
                x++;
                pixel++;
            }
        }
        std::cout << "\rprogress: done\t" << std::endl;
        // iterate over every pixel
        for (const auto& pixel : {image.begin<cv::Vec3b>(), image.end<cv::Vec3b>()})
            *pixel = pixel_closest_colour(colors, *pixel, norm);
    }
}


void generateDitheredImage(const std::string& image_path, const std::string& out_path)
{
    cv::Mat img = cv::imread(image_path, cv::IMREAD_COLOR);
    dither::ditherImage(dither::palettes::waveshare7color, img, dither::STEVENSON_ARCE, cv::NORM_L1);
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
