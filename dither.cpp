#include <opencv2/opencv.hpp>
#include <vector>
#include <optional>


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


    cv::Vec3b pixel_closest_colour(const std::list<cv::Vec3b>& palette, const cv::Vec3b& old_pixel,
                                   const cv::NormTypes norm)
    {
        std::optional<cv::Vec3b> closest_colour = std::nullopt;
        auto min_distance = std::numeric_limits<double>::max();
        for (const auto& color : palette)
        {
            if (const auto distance = cv::norm(old_pixel, color, norm); distance < min_distance)
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
        std::cout.precision(2);
        auto diff_map = getDiffusionMap(method);

        for (auto y = 0; y < image.rows; y++)
        {
            for (auto x = 0; x < image.cols; x++)
            {
                if (x == image.cols - 1 && y % (image.rows / 10) == 0)
                    std::cout << "progress: " << 1.0 * x * y / (image.rows * image.cols) << std::endl;
                auto old_pixel = image.at<cv::Vec3b>(y, x);
                auto new_pixel = pixel_closest_colour(palette, old_pixel, norm);
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
    }
}

void generateDitheredImage(const std::string& image_path, const std::string& out_path)
{
    cv::Mat img = cv::imread(image_path, cv::IMREAD_COLOR);
    const auto palette = std::list<cv::Vec3b>{
        {0, 0, 0},
        {255, 255, 255},
        {0, 255, 0},
        {0, 0, 255},
        {255, 0, 0},
        {255, 255, 0},
        {255, 128, 0}
    };
    dither::ditherImage(palette, img, dither::STEVENSON_ARCE, cv::NORM_L2);
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
