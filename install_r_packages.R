# Install required R packages for democracy analysis
packages_needed <- c("gamlss", "mice", "dplyr", "broom.mixed", "jsonlite", "VIM")

# Function to install packages if not already installed
install_if_missing <- function(pkg) {
  if (!require(pkg, character.only = TRUE)) {
    cat("Installing package:", pkg, "\n")
    install.packages(pkg, repos = "https://cran.rstudio.com/", 
                     dependencies = TRUE, quiet = FALSE)
    library(pkg, character.only = TRUE)
  } else {
    cat("Package", pkg, "already installed\n")
  }
}

# Install all packages
for (pkg in packages_needed) {
  install_if_missing(pkg)
}

cat("All R packages installed successfully!\n")
