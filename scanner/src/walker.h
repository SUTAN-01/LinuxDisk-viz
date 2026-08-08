#pragma once
#include <string>
#include <vector>
#include <functional>

void walk(const std::string& root,
          std::function<void(const std::string&)> callback,
          const std::vector<std::string>& excludes = {},
          bool follow_symlinks = false);
