#include <opencv2/opencv.hpp>
#include <vector>
#include <optional>
#include <map>
#include <random>
#include <list>
#include <algorithm>
#include <iostream>

namespace dither
{
    enum method
    {
        FLOYD_STEINBERG,
        JARVIS_JUDICE_NINKE,
        STUCKI,
        BURKES,
        SIERRA,
        SIERRA_2,
        SIERRA_3,
        ATKINSON,
        STEVENSON_ARCE
    };

    using BGR = cv::Vec3b;
    std::map<std::string, BGR> color_map = {
        {"Black", {0, 0, 0}},
        {"White", {255, 255, 255}},
        {"Green", {0, 255, 0}},
        {"Blue", {255, 0, 0}},
        {"Red", {0, 0, 255}},
        {"Yellow", {0, 255, 255}},
        {"Orange", {0, 128, 255}}
    };

    std::vector<std::tuple<int, int, float>> getDiffusionMap(const method name)
    {
        if (name == FLOYD_STEINBERG)
        {
            return {
                {1, 0, 7.0 / 16.0},
                {-1, 1, 3.0 / 16.0},
                {0, 1, 5.0 / 16.0},
                {1, 1, 1.0 / 16.0}
            };
        }
        if (name == JARVIS_JUDICE_NINKE)
        {
            return {
                {1, 0, 7.0 / 48.0},
                {2, 0, 5.0 / 48.0},
                {-2, 1, 3.0 / 48.0},
                {-1, 1, 5.0 / 48.0},
                {0, 1, 7.0 / 48.0},
                {1, 1, 5.0 / 48.0},
                {2, 1, 3.0 / 48.0},
                {-2, 2, 1.0 / 48.0},
                {-1, 2, 3.0 / 48.0},
                {0, 2, 5.0 / 48.0},
                {1, 2, 3.0 / 48.0},
                {2, 2, 1.0 / 48.0}
            };
        }
        if (name == STUCKI)
        {
            return {
                {1, 0, 8.0 / 42.0},
                {2, 0, 4.0 / 42.0},
                {-2, 1, 2.0 / 42.0},
                {-1, 1, 4.0 / 42.0},
                {0, 1, 8.0 / 42.0},
                {1, 1, 4.0 / 42.0},
                {2, 1, 2.0 / 42.0},
                {-2, 2, 1.0 / 42.0},
                {-1, 2, 2.0 / 42.0},
                {0, 2, 4.0 / 42.0},
                {1, 2, 2.0 / 42.0},
                {2, 2, 1.0 / 42.0}
            };
        }
        if (name == BURKES)
        {
            return {
                {1, 0, 8.0 / 32.0},
                {2, 0, 4.0 / 32.0},
                {-2, 1, 2.0 / 32.0},
                {-1, 1, 4.0 / 32.0},
                {0, 1, 8.0 / 32.0},
                {1, 1, 4.0 / 32.0},
                {2, 1, 2.0 / 32.0}
            };
        }
        if (name == SIERRA)
        {
            return {
                {1, 0, 5.0 / 32.0},
                {2, 0, 3.0 / 32.0},
                {-2, 1, 2.0 / 32.0},
                {-1, 1, 4.0 / 32.0},
                {0, 1, 5.0 / 32.0},
                {1, 1, 4.0 / 32.0},
                {2, 1, 2.0 / 32.0},
                {-1, 2, 2.0 / 32.0},
                {0, 2, 3.0 / 32.0},
                {1, 2, 2.0 / 32.0}
            };
        }
        if (name == SIERRA_2)
        {
            return {
                {1, 0, 4.0 / 16.0},
                {2, 0, 3.0 / 16.0},
                {-2, 1, 1.0 / 16.0},
                {-1, 1, 2.0 / 16.0},
                {0, 1, 3.0 / 16.0},
                {1, 1, 2.0 / 16.0},
                {2, 1, 1.0 / 16.0}
            };
        }
        if (name == SIERRA_3)
        {
            return std::vector<std::tuple<int, int, float>>{
                {1, 0, 5.0 / 32.0},
                {2, 0, 3.0 / 32.0},
                {-2, 1, 2.0 / 32.0},
                {-1, 1, 4.0 / 32.0},
                {0, 1, 5.0 / 32.0},
                {1, 1, 4.0 / 32.0},
                {2, 1, 2.0 / 32.0}
            };
        }
        if (name == ATKINSON)
        {
            return {
                {1, 0, 1.0 / 8.0},
                {2, 0, 1.0 / 8.0},
                {-1, 1, 1.0 / 8.0},
                {0, 1, 1.0 / 8.0},
                {1, 1, 1.0 / 8.0},
                {0, 2, 1.0 / 8.0}
            };
        }
        if (name == STEVENSON_ARCE)
        {
            return {
                {1, 0, 32.0 / 200.0},
                {2, 0, 12.0 / 200.0},
                {-2, 1, 5.0 / 200.0},
                {-1, 1, 12.0 / 200.0},
                {0, 1, 32.0 / 200.0},
                {1, 1, 12.0 / 200.0},
                {2, 1, 5.0 / 200.0},
                {-2, 2, 2.0 / 200.0},
                {-1, 2, 5.0 / 200.0},
                {0, 2, 12.0 / 200.0},
                {1, 2, 5.0 / 200.0},
                {2, 2, 2.0 / 200.0}
            };
        }
        assert(false);
        return {};
    }

    double colorDistance(const cv::Vec3b& color1, const cv::Vec3b& color2, cv::NormTypes norm)
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
        std::random_device rd;
        std::mt19937 g(rd());
        std::shuffle(palette.begin(), palette.end(), g);
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
                     const method method = FLOYD_STEINBERG, cv::NormTypes norm = cv::NORM_L2)
    {
        std::vector<cv::Vec3b> colors = {palette.begin(), palette.end()};
        std::cout.precision(2);
        auto diff_map = getDiffusionMap(method);

        for (auto y = 0; y < image.rows; y++)
        {
            for (auto x = 0; x < image.cols; x++)
            {
                if (x == image.cols - 1 && y % (image.rows / 10) == 0)
                    std::cout << "progress: " << 1.0 * x * y / (image.rows * image.cols) << std::endl;
                auto old_pixel = image.at<cv::Vec3b>(y, x);
                auto new_pixel = pixel_closest_colour(colors, old_pixel, norm);
                auto quantization_error = old_pixel - new_pixel;
                image.at<cv::Vec3b>(y, x) = new_pixel;
                for (auto [dx, dy, diffusion_coefficient] : diff_map)
                {
                    const auto xn = x + dx;
                    const auto yn = y + dy;
                    if ((0 <= xn && xn < image.cols) && (0 <= yn && yn < image.rows))
                    {
                        image.at<cv::Vec3b>(yn, xn) += quantization_error * diffusion_coefficient;
                    }
                }
            }
        }
        // iterate over every pixel
        for (const auto& pixel : {image.begin<cv::Vec3b>(), image.end<cv::Vec3b>()})
        {
            *pixel = pixel_closest_colour(colors, *pixel, norm);
        }
    }
}

void generateDitheredImage(const std::string& image_path, const std::string& out_path)
{
    cv::Mat img = cv::imread(image_path, cv::IMREAD_COLOR);
    const auto palette = std::list{
        dither::color_map["Black"],
        dither::color_map["White"],
        dither::color_map["Green"],
        dither::color_map["Blue"],
        dither::color_map["Red"],
        dither::color_map["Yellow"],
        dither::color_map["Orange"]
    };
    dither::ditherImage(palette, img, dither::STEVENSON_ARCE, cv::NORM_INF);
    cv::imwrite(out_path, img);
}

int main(const int argc, char** argv)
{
    if (argc != 3)
    {
        std::cerr << "Usage: " << argv[0] << " <input_image_path> <output_image_path>" << std::endl;
        return 1;
    }
    const std::string image_path = argv[1];
    const std::string out_path = argv[2];
    generateDitheredImage(image_path, out_path);
}
