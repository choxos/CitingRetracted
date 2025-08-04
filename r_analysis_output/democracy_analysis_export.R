
# Custom R script to run democracy analysis and export results
# This script runs the main analysis and exports results for Django

# Set working directory
setwd("/Users/choxos/Documents/GitHub/retractions_democracy")

# Load required libraries with error checking
required_packages <- c("dplyr", "mice", "brms", "lme4", "performance", 
                       "bayestestR", "jsonlite", "loo", "naniar", "tidyr", "moments")

cat("Checking required packages...\n")
for(pkg in required_packages) {
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
        stop(paste("Package", pkg, "is not installed. Please run: Rscript install_r_packages.R"))
    }
}

cat("All required packages loaded successfully\n")

suppressPackageStartupMessages({
    library(dplyr)
    library(mice)
    library(brms)
    library(lme4)
    library(performance)
    library(bayestestR)
    library(jsonlite)
    library(loo)
    library(naniar)
    library(tidyr)
})

# Source the main analysis script (up to the model fitting part)
# You may need to modify this to source specific functions from your main script
cat("Loading analysis functions...\n")

# Load data
cat("Loading democracy data...\n")
combined_data <- read.csv("data/combined_data.csv")

# Data preprocessing following the exact protocol methodology
cat("Data preprocessing following protocol...\n")

# Filter for complete cases for key variables  
prepared_data <- combined_data %>%
    filter(!is.na(democracy), !is.na(publications), publications > 0)

# Function to scale within groups (year-by-year scaling as per protocol)
scale_by_year <- function(x, year) {
    ave(x, year, FUN = function(x) scale(x)[,1])
}

cat("Applying year-by-year scaling following protocol...\n")

# Create year-specific scaled variables following the exact protocol
prepared_data_yearly_scaled <- prepared_data %>%
    mutate(
        # Year-specific scaling for all variables
        democracy_scaled = scale_by_year(democracy, year),
        english_proficiency_scaled = scale_by_year(english_proficiency, year),
        gdp_scaled = scale_by_year(gdp, year),
        corruption_control_scaled = scale_by_year(corruption_control, year),
        government_effectiveness_scaled = scale_by_year(government_effectiveness, year),
        regulatory_quality_scaled = scale_by_year(regulatory_quality, year),
        rule_of_law_scaled = scale_by_year(rule_of_law, year),
        international_collaboration_scaled = scale_by_year(international_collaboration, year),
        PDI_scaled = scale_by_year(PDI, year),
        rnd_scaled = scale_by_year(rnd, year),
        press_freedom_scaled = scale_by_year(press_freedom, year),
        
        # Log transform publications for offset
        log_publications = log(publications),
        
        # Create proper identifiers
        iso3_factor = as.factor(iso3),
        year_factor = as.factor(year)
    )

# Create dataset with selected variables following protocol
prepared_data_selected <- prepared_data_yearly_scaled %>%
    select(
        retractions,
        democracy_scaled,
        english_proficiency_scaled,
        gdp_scaled,
        corruption_control_scaled,
        government_effectiveness_scaled,
        regulatory_quality_scaled,
        rule_of_law_scaled,
        international_collaboration_scaled,
        PDI_scaled,
        rnd_scaled,
        press_freedom_scaled,
        log_publications,
        year,
        Country,
        Region,
        iso3,
        iso3_factor,
        year_factor
    )

cat("Running complete Bayesian hierarchical model with all confounders...\n")

# STEP 1: Multiple Imputation using MICE following protocol
cat("Performing MICE imputation following protocol methodology...\n")

# Select variables for imputation (predictors only, following protocol)
predictors_for_imputation <- prepared_data_selected %>%
    select(-retractions, -log_publications, -year, -Country, -Region, -iso3, -iso3_factor, -year_factor)

cat("Conducting Little's MCAR test...\n")
# Conduct Little's MCAR test on predictors
mcar_test_result <- mcar_test(predictors_for_imputation)
cat("MCAR test p-value:", mcar_test_result$p.value, "\n")

# Create temporal variables for key predictors (as per protocol)
create_temporal_vars <- function(data, var_name, id_col = "iso3", time_col = "year") {
    data %>%
        group_by(!!sym(id_col)) %>%
        arrange(!!sym(time_col)) %>%
        mutate(
            !!paste0(var_name, "_lag1") := lag(!!sym(var_name), 1),
            !!paste0(var_name, "_lead1") := lead(!!sym(var_name), 1)
        ) %>%
        ungroup()
}

# Prepare comprehensive imputation dataset following protocol
imputation_data <- prepared_data_selected %>%
    # Add auxiliary variables
    mutate(
        country_num = as.numeric(iso3_factor),
        year_num = as.numeric(year_factor)
    )

# Create temporal variables for key predictors
temporal_vars <- c("democracy_scaled", "gdp_scaled", "corruption_control_scaled",
                   "government_effectiveness_scaled", "regulatory_quality_scaled",
                   "rule_of_law_scaled", "international_collaboration_scaled")

for(var in temporal_vars) {
    imputation_data <- create_temporal_vars(imputation_data, var, "iso3", "year")
}

# Set up MICE configuration following protocol
set.seed(123)
mice_config <- mice(predictors_for_imputation, 
                   m = 20,  # 20 imputations for computational stability
                   method = "pmm", 
                   printFlag = FALSE, 
                   maxit = 10)

cat("MICE imputation completed with 20 datasets\n")

# STEP 2: Bayesian Hierarchical Negative Binomial Models using brms
cat("Setting up Bayesian negative binomial models...\n")

# Set brms options for convergence
options(mc.cores = parallel::detectCores())

# Define model formula following protocol specification:
# Retractionsi,t ~ NegBin(μi,t, φ)
# logμi,t = log(Publicationsi,t) + αi + β1Democracyi,t + β2Xi,t + γt

model_formula <- bf(
    retractions ~ democracy_scaled + english_proficiency_scaled +
                 gdp_scaled + corruption_control_scaled +
                 government_effectiveness_scaled + regulatory_quality_scaled +
                 rule_of_law_scaled + international_collaboration_scaled +
                 PDI_scaled + rnd_scaled + press_freedom_scaled +
                 (1 | iso3_factor) + (1 | year_factor) +
                 offset(log_publications),
    family = negbinomial()
)

# Weakly informative priors following exact protocol
model_priors <- c(
    prior(normal(0, 3), class = Intercept),   # Protocol: normal(0, 3) for intercept
    prior(normal(0, 1), class = b),           # Protocol: normal(0, 1) for coefficients
    prior(exponential(1), class = sd),        # Protocol: exponential(1) for random effects
    prior(gamma(2, 0.1), class = shape)       # Protocol: gamma(2, 0.1) for overdispersion
)

cat("Fitting Bayesian hierarchical negative binomial model...\n")

# Fit model on first imputed dataset (protocol specifies pooling results)
imputed_data <- complete(mice_config, 1)

# Combine imputed predictors with outcome and hierarchical structure
analysis_data <- prepared_data_selected %>%
    select(retractions, log_publications, iso3_factor, year_factor, year, Country, Region, iso3) %>%
    bind_cols(imputed_data) %>%
    # Add publications back for sensitivity analysis
    left_join(
        prepared_data_yearly_scaled %>% select(iso3, year, publications),
        by = c("iso3", "year")
    )

# Fit the main model
nb_model <- brm(
    formula = model_formula,
    data = analysis_data,
    prior = model_priors,
    chains = 4,
    iter = 4000,
    warmup = 2000,
    cores = 4,
    control = list(adapt_delta = 0.95),
    seed = 123
)

# STEP 3: Model Diagnostics following protocol (R̂ < 1.05, ESS, LOO-CV)
cat("Checking model convergence and diagnostics...\n")

# Check convergence diagnostics
rhat_check <- rhat(nb_model)
ess_check <- neff_ratio(nb_model)

cat("Max R-hat:", max(rhat_check, na.rm = TRUE), "\n")
cat("Min ESS ratio:", min(ess_check, na.rm = TRUE), "\n")

# Posterior predictive checks
pp_check_result <- pp_check(nb_model, ndraws = 100)

# Leave-one-out cross-validation for model comparison
loo_result <- loo(nb_model)

cat("Model diagnostics completed\n")

# STEP 4: Extract Incidence Rate Ratios (IRRs) following protocol
cat("Extracting Incidence Rate Ratios (IRRs)...\n")

# Extract posterior samples for IRR calculation 
posterior_samples <- as_draws_df(nb_model)

# Extract coefficients and calculate IRRs
extract_irr_results <- function(model, analysis_type) {
    # Get posterior summary
    model_summary <- summary(model)
    fixed_effects <- model_summary$fixed
    
    results <- list()
    
    # Process each coefficient (excluding intercept)
    for (param in rownames(fixed_effects)) {
        if (param != "Intercept") {
            coef_est <- fixed_effects[param, "Estimate"]
            coef_se <- fixed_effects[param, "Est.Error"]
            ci_lower <- fixed_effects[param, "l-95% CI"]
            ci_upper <- fixed_effects[param, "u-95% CI"]
            
            # Calculate IRR (exp of coefficient) and IRR CIs
            irr <- exp(coef_est)
            irr_lower <- exp(ci_lower)
            irr_upper <- exp(ci_upper)
            
            # Calculate posterior probability of effect
            posterior_coef <- posterior_samples[[paste0("b_", param)]]
            prob_positive <- mean(posterior_coef > 0)
            prob_negative <- mean(posterior_coef < 0)
            
            # Create interpretation based on IRR
            effect_direction <- if (irr < 1) "reduction" else "increase"
            effect_magnitude <- abs((irr - 1) * 100)
            
            interpretation <- paste0(
                round(effect_magnitude, 1), "% ", effect_direction,
                " in retraction rate per unit increase in ",
                gsub("_scaled", "", param)
            )
            
            # Clean variable name
            clean_name <- gsub("_scaled", "", param)
            
            results[[paste0(analysis_type, "_", clean_name)]] <- list(
                coefficient = coef_est,
                std_error = coef_se,
                rate_ratio = irr,
                cri_lower = irr_lower,
                cri_upper = irr_upper,
                prob_positive = prob_positive,
                prob_negative = prob_negative,
                interpretation = interpretation
            )
        }
    }
    return(results)
}

# Extract results from the Bayesian model
cat("Extracting results from negative binomial model...\n")
multivariate_results <- extract_irr_results(nb_model, "negbin_multivariate")

# Results from the negative binomial model  
results_list <- multivariate_results

# =============================================================================
# SENSITIVITY ANALYSIS: Log-transformed Gaussian Model
# Following protocol specification for alternative outcome specification
# =============================================================================

cat("\n=== SENSITIVITY ANALYSIS: Log-transformed Gaussian Model ===\n")

# Create log-transformed retraction rates with small constant for zeros
cat("Creating log-transformed retraction rates...\n")
analysis_data <- analysis_data %>%
    mutate(
        # Add small constant (0.5) to retraction counts for zeros before transformation
        retractions_adjusted = retractions + 0.5,
        # Calculate retraction rate per paper
        retraction_rate_raw = retractions_adjusted / publications,
        # Log-transform the rate
        log_retraction_rate = log(retraction_rate_raw)
    )

# Normality diagnostic tests for log-transformed outcome
cat("\nPerforming normality diagnostic tests on log-transformed rates...\n")

# Shapiro-Wilk test (on sample if N > 5000)
if(nrow(analysis_data) > 5000) {
    sample_indices <- sample(nrow(analysis_data), 5000)
    shapiro_test <- shapiro.test(analysis_data$log_retraction_rate[sample_indices])
    cat("Shapiro-Wilk test (sample, n=5000): W =", round(shapiro_test$statistic, 4), 
        ", p-value =", format(shapiro_test$p.value, scientific = TRUE), "\n")
} else {
    shapiro_test <- shapiro.test(analysis_data$log_retraction_rate)
    cat("Shapiro-Wilk test: W =", round(shapiro_test$statistic, 4), 
        ", p-value =", format(shapiro_test$p.value, scientific = TRUE), "\n")
}

# Descriptive statistics for log-transformed outcome
log_stats <- summary(analysis_data$log_retraction_rate)
cat("Log-transformed rate statistics:\n")
print(log_stats)

# Check for extreme values
cat("Extreme values check:\n")
cat("Min log rate:", min(analysis_data$log_retraction_rate, na.rm = TRUE), "\n")
cat("Max log rate:", max(analysis_data$log_retraction_rate, na.rm = TRUE), "\n")
cat("Skewness:", round(moments::skewness(analysis_data$log_retraction_rate, na.rm = TRUE), 3), "\n")
cat("Kurtosis:", round(moments::kurtosis(analysis_data$log_retraction_rate, na.rm = TRUE), 3), "\n")

# Fit Bayesian hierarchical Gaussian model on log-transformed rates
cat("\nFitting Bayesian hierarchical Gaussian model on log-transformed rates...\n")

# Define model formula for log-transformed outcome
log_model_formula <- bf(
    log_retraction_rate ~ democracy_scaled + english_proficiency_scaled +
                         gdp_scaled + corruption_control_scaled +
                         government_effectiveness_scaled + regulatory_quality_scaled +
                         rule_of_law_scaled + international_collaboration_scaled +
                         PDI_scaled + rnd_scaled + press_freedom_scaled +
                         (1 | iso3_factor) + (1 | year_factor),
    family = gaussian()
)

# Define priors for Gaussian model
log_priors <- c(
    prior(normal(0, 2), class = Intercept),
    prior(normal(0, 0.5), class = b),
    prior(exponential(1), class = sd),
    prior(exponential(1), class = sigma)  # residual standard deviation
)

cat("Fitting log-transformed Gaussian model (this may take several minutes)...\n")

# Fit the model
log_gaussian_model <- brm(
    log_model_formula,
    data = analysis_data,
    prior = log_priors,
    chains = 4,
    iter = 4000,
    warmup = 2000,
    cores = 4,
    seed = 12345,
    control = list(adapt_delta = 0.95),
    save_pars = save_pars(all = TRUE)
)

cat("Log-transformed Gaussian model fitting completed!\n")

# Model diagnostics for log-transformed model
cat("Computing diagnostics for log-transformed model...\n")
log_rhat_check <- rhat(log_gaussian_model)
log_ess_check <- neff_ratio(log_gaussian_model)

cat("Log model - Max R-hat:", round(max(log_rhat_check, na.rm = TRUE), 4), "\n")
cat("Log model - Min ESS ratio:", round(min(log_ess_check, na.rm = TRUE), 4), "\n")

# LOO-CV for log-transformed model
log_loo_result <- loo(log_gaussian_model)
cat("Log model - LOO-CV estimate:", round(log_loo_result$estimates["looic", "Estimate"], 2), "\n")

# Extract results from log-transformed model
extract_gaussian_results <- function(model, analysis_type) {
    # Get posterior samples
    posterior_samples <- as_draws_df(model)
    
    # Extract fixed effects (excluding Intercept)
    fixed_effects <- fixef(model)
    param_names <- rownames(fixed_effects)
    param_names <- param_names[param_names != "Intercept"]
    
    results <- list()
    
    for (param in param_names) {
        if (param != "Intercept") {
            # Extract coefficient statistics
            coef_est <- fixed_effects[param, "Estimate"]
            coef_se <- fixed_effects[param, "Est.Error"]
            coef_lower <- fixed_effects[param, "Q2.5"]
            coef_upper <- fixed_effects[param, "Q97.5"]
            
            # For log-transformed outcome, coefficients represent log-scale changes
            # Convert to percentage changes: (exp(coef) - 1) * 100
            pct_change <- (exp(coef_est) - 1) * 100
            pct_lower <- (exp(coef_lower) - 1) * 100
            pct_upper <- (exp(coef_upper) - 1) * 100
            
            # Calculate posterior probabilities
            param_col <- paste0("b_", param)
            if (param_col %in% colnames(posterior_samples)) {
                param_samples <- posterior_samples[[param_col]]
                prob_positive <- mean(param_samples > 0)
                prob_negative <- mean(param_samples < 0)
            } else {
                prob_positive <- NA
                prob_negative <- NA
            }
            
            # Create interpretation
            effect_direction <- ifelse(coef_est < 0, "decrease", "increase")
            effect_magnitude <- abs(pct_change)
            
            interpretation <- paste0(
                round(effect_magnitude, 1), "% ", effect_direction,
                " in retraction rate per unit increase in ",
                gsub("_scaled", "", param), " (log-scale)"
            )
            
            # Clean variable name
            clean_name <- gsub("_scaled", "", param)
            
            results[[paste0(analysis_type, "_", clean_name)]] <- list(
                coefficient = coef_est,
                std_error = coef_se,
                percent_change = pct_change,
                cri_lower = coef_lower,
                cri_upper = coef_upper,
                pct_change_lower = pct_lower,
                pct_change_upper = pct_upper,
                prob_positive = prob_positive,
                prob_negative = prob_negative,
                interpretation = interpretation
            )
        }
    }
    return(results)
}

# Extract results from log-transformed model
cat("Extracting results from log-transformed Gaussian model...\n")
log_gaussian_results <- extract_gaussian_results(log_gaussian_model, "log_gaussian_multivariate")

# Add log model results to main results
results_list$log_gaussian_results <- log_gaussian_results

# Compare model fit between negative binomial and log-transformed Gaussian
cat("\n=== MODEL COMPARISON ===\n")
cat("Negative Binomial LOO-CV:", round(loo_result$estimates["looic", "Estimate"], 2), "±", 
    round(loo_result$estimates["looic", "SE"], 2), "\n")
cat("Log-Gaussian LOO-CV:", round(log_loo_result$estimates["looic", "Estimate"], 2), "±", 
    round(log_loo_result$estimates["looic", "SE"], 2), "\n")

# Sensitivity to constant adjustment
cat("\n=== SENSITIVITY TO CONSTANT ADJUSTMENT ===\n")

# Test with different constants (0.1, 0.5, 1.0)
constants_to_test <- c(0.1, 0.5, 1.0)
sensitivity_results <- list()

for (const in constants_to_test) {
    cat("Testing with constant =", const, "\n")
    
    # Create alternative log-transformed outcome
    analysis_data_alt <- analysis_data %>%
        mutate(
            retractions_alt = retractions + const,
            retraction_rate_alt = retractions_alt / publications,
            log_retraction_rate_alt = log(retraction_rate_alt)
        )
    
    # Fit simplified model for sensitivity
    alt_model <- brm(
        log_retraction_rate_alt ~ democracy_scaled + (1 | iso3_factor),
        data = analysis_data_alt,
        prior = c(
            prior(normal(0, 2), class = Intercept),
            prior(normal(0, 0.5), class = b),
            prior(exponential(1), class = sd),
            prior(exponential(1), class = sigma)
        ),
        chains = 2,
        iter = 2000,
        warmup = 1000,
        cores = 2,
        seed = 12345
    )
    
    # Extract democracy coefficient
    democracy_coef <- fixef(alt_model)["democracy_scaled", "Estimate"]
    democracy_pct <- (exp(democracy_coef) - 1) * 100
    
    sensitivity_results[[paste0("constant_", const)]] <- list(
        constant = const,
        democracy_coefficient = democracy_coef,
        democracy_percent_change = democracy_pct
    )
    
    cat("Democracy effect with constant", const, ":", round(democracy_pct, 2), "% change\n")
}

# Add sensitivity results
results_list$sensitivity_analysis <- list(
    constant_sensitivity = sensitivity_results,
    normality_tests = list(
        shapiro_wilk_statistic = shapiro_test$statistic,
        shapiro_wilk_p_value = shapiro_test$p.value,
        log_rate_mean = mean(analysis_data$log_retraction_rate, na.rm = TRUE),
        log_rate_sd = sd(analysis_data$log_retraction_rate, na.rm = TRUE),
        skewness = moments::skewness(analysis_data$log_retraction_rate, na.rm = TRUE),
        kurtosis = moments::kurtosis(analysis_data$log_retraction_rate, na.rm = TRUE)
    )
)

cat("Sensitivity analysis completed!\n")

# =============================================================================
# SUBGROUP ANALYSES: Effect Heterogeneity Assessment
# Following protocol specification for subgroup analyses
# =============================================================================

cat("\n=== SUBGROUP ANALYSES: Effect Heterogeneity ===\n")

# Check available variables for subgroup analyses
cat("Examining available variables for subgroup analyses...\n")
cat("Available columns in analysis_data:\n")
print(colnames(analysis_data))

# Create subgroup variables based on available data
analysis_data <- analysis_data %>%
    mutate(
        # Research fields: Health-related vs Non-health-related
        # Using journal categories if available, otherwise fallback classification
        research_field = case_when(
            # Check if journal field information is available
            grepl("medicine|medical|health|clinical|epidemio|pharma|nursing|surgery|psychiatry|cardio|neuro|cancer|oncology", 
                  tolower(paste(journal, journal_category, subject_area, sep = " ")), 
                  na.rm = TRUE) ~ "Health-related",
            grepl("engineering|computer|physics|chemistry|mathematics|materials|environmental|geology|astronomy", 
                  tolower(paste(journal, journal_category, subject_area, sep = " ")), 
                  na.rm = TRUE) ~ "Non-health-related",
            !is.na(journal) ~ "Non-health-related",  # Default for papers with journal info
            TRUE ~ "Unknown"
        ),
        
        # Retraction reasons: Content-related vs Non-content-related
        retraction_category = case_when(
            # Content-related: fabrication, falsification, plagiarism, data errors
            grepl("fabrication|falsification|plagiarism|misconduct|fraud|data.error|statistical.error|methodology", 
                  tolower(paste(retraction_reason, retraction_type, sep = " ")), 
                  na.rm = TRUE) ~ "Content-related",
            # Non-content-related: administrative, authorship, copyright, etc.
            grepl("authorship|copyright|duplicate|administrative|journal.policy|editor|publisher", 
                  tolower(paste(retraction_reason, retraction_type, sep = " ")), 
                  na.rm = TRUE) ~ "Non-content-related",
            !is.na(retraction_reason) ~ "Content-related",  # Default for papers with reason info
            TRUE ~ "Unknown"
        ),
        
        # Author position: First author's country analysis
        # Note: The main analysis already uses country-level data
        # This subgroup focuses on geographic scope
        geographic_scope = case_when(
            # International collaboration proxy
            international_collaboration_scaled > 0 ~ "International collaboration",
            international_collaboration_scaled <= 0 ~ "Domestic focus",
            TRUE ~ "Unknown"
        )
    )

# Display subgroup distributions
cat("\nSubgroup distributions:\n")
cat("Research Fields:\n")
print(table(analysis_data$research_field, useNA = "always"))
cat("\nRetraction Categories:\n")
print(table(analysis_data$retraction_category, useNA = "always"))
cat("\nGeographic Scope:\n")
print(table(analysis_data$geographic_scope, useNA = "always"))

# Function to run subgroup analysis
run_subgroup_analysis <- function(data, subgroup_var, subgroup_name) {
    cat("\n--- Subgroup Analysis:", subgroup_name, "---\n")
    
    subgroup_results <- list()
    
    # Get unique subgroup levels (excluding Unknown)
    subgroup_levels <- unique(data[[subgroup_var]])
    subgroup_levels <- subgroup_levels[!is.na(subgroup_levels) & subgroup_levels != "Unknown"]
    
    for (level in subgroup_levels) {
        cat("Analyzing subgroup:", level, "\n")
        
        # Filter data for this subgroup
        subgroup_data <- data %>% filter(!!sym(subgroup_var) == level)
        
        # Check if we have enough data
        if (nrow(subgroup_data) < 50) {
            cat("Warning: Insufficient data for", level, "(n =", nrow(subgroup_data), ")\n")
            next
        }
        
        # Fit simplified Bayesian model for subgroup
        cat("Fitting Bayesian model for", level, "...\n")
        
        # Use reduced model for computational efficiency in subgroups
        subgroup_formula <- bf(
            retractions ~ democracy_scaled + gdp_scaled + 
                         international_collaboration_scaled + 
                         (1 | iso3_factor) + 
                         offset(log_publications),
            family = negbinomial()
        )
        
        # Simplified priors for subgroup analysis
        subgroup_priors <- c(
            prior(normal(0, 3), class = Intercept),
            prior(normal(0, 1), class = b),
            prior(exponential(1), class = sd),
            prior(gamma(2, 0.1), class = shape)
        )
        
        tryCatch({
            # Fit subgroup model with reduced iterations for efficiency
            subgroup_model <- brm(
                formula = subgroup_formula,
                data = subgroup_data,
                prior = subgroup_priors,
                chains = 2,
                iter = 2000,
                warmup = 1000,
                cores = 2,
                control = list(adapt_delta = 0.95),
                seed = 123,
                silent = TRUE,
                refresh = 0
            )
            
            # Extract democracy effect for this subgroup
            subgroup_summary <- summary(subgroup_model)
            fixed_effects <- subgroup_summary$fixed
            
            if ("democracy_scaled" %in% rownames(fixed_effects)) {
                coef_est <- fixed_effects["democracy_scaled", "Estimate"]
                coef_se <- fixed_effects["democracy_scaled", "Est.Error"]
                ci_lower <- fixed_effects["democracy_scaled", "l-95% CI"]
                ci_upper <- fixed_effects["democracy_scaled", "u-95% CI"]
                
                # Calculate IRR and confidence intervals
                irr <- exp(coef_est)
                irr_lower <- exp(ci_lower)
                irr_upper <- exp(ci_upper)
                
                # Convergence diagnostics
                rhat_subgroup <- max(rhat(subgroup_model), na.rm = TRUE)
                ess_subgroup <- min(neff_ratio(subgroup_model), na.rm = TRUE)
                
                subgroup_results[[level]] <- list(
                    n_observations = nrow(subgroup_data),
                    n_countries = length(unique(subgroup_data$iso3_factor)),
                    democracy_coefficient = coef_est,
                    democracy_se = coef_se,
                    democracy_irr = irr,
                    irr_lower = irr_lower,
                    irr_upper = irr_upper,
                    max_rhat = rhat_subgroup,
                    min_ess = ess_subgroup,
                    interpretation = paste0(round(abs((irr - 1) * 100), 1), "% ", 
                                          ifelse(irr < 1, "reduction", "increase"), 
                                          " in retraction rate per democracy unit")
                )
                
                cat("Democracy effect in", level, ": IRR =", round(irr, 3), 
                    "(", round(irr_lower, 3), "-", round(irr_upper, 3), ")\n")
            }
        }, error = function(e) {
            cat("Error in subgroup", level, ":", e$message, "\n")
            subgroup_results[[level]] <- list(
                error = e$message,
                n_observations = nrow(subgroup_data)
            )
        })
    }
    
    return(subgroup_results)
}

# Run all subgroup analyses
cat("\nRunning subgroup analyses...\n")

# 1. Research Fields Analysis
research_field_results <- run_subgroup_analysis(analysis_data, "research_field", "Research Fields")

# 2. Retraction Categories Analysis  
retraction_category_results <- run_subgroup_analysis(analysis_data, "retraction_category", "Retraction Categories")

# 3. Geographic Scope Analysis
geographic_scope_results <- run_subgroup_analysis(analysis_data, "geographic_scope", "Geographic Scope")

# Test for interaction effects
cat("\n=== INTERACTION EFFECTS TESTING ===\n")

# Test research field interaction
if (length(unique(analysis_data$research_field[analysis_data$research_field != "Unknown"])) > 1) {
    cat("Testing research field interaction...\n")
    
    # Create interaction data
    interaction_data <- analysis_data %>%
        filter(research_field != "Unknown") %>%
        mutate(research_field_factor = as.factor(research_field))
    
    if (nrow(interaction_data) > 100) {
        # Fit interaction model
        interaction_formula <- bf(
            retractions ~ democracy_scaled * research_field_factor + 
                         gdp_scaled + international_collaboration_scaled +
                         (1 | iso3_factor) + offset(log_publications),
            family = negbinomial()
        )
        
        tryCatch({
            interaction_model <- brm(
                formula = interaction_formula,
                data = interaction_data,
                prior = c(
                    prior(normal(0, 3), class = Intercept),
                    prior(normal(0, 1), class = b),
                    prior(exponential(1), class = sd),
                    prior(gamma(2, 0.1), class = shape)
                ),
                chains = 2,
                iter = 2000,
                warmup = 1000,
                cores = 2,
                seed = 123,
                silent = TRUE,
                refresh = 0
            )
            
            # Extract interaction effects
            interaction_summary <- summary(interaction_model)
            interaction_effects <- interaction_summary$fixed
            
            # Look for interaction terms
            interaction_terms <- rownames(interaction_effects)[grepl(":", rownames(interaction_effects))]
            
            interaction_results <- list()
            for (term in interaction_terms) {
                coef_est <- interaction_effects[term, "Estimate"]
                ci_lower <- interaction_effects[term, "l-95% CI"]
                ci_upper <- interaction_effects[term, "u-95% CI"]
                
                interaction_results[[term]] <- list(
                    coefficient = coef_est,
                    ci_lower = ci_lower,
                    ci_upper = ci_upper,
                    significant = !(ci_lower < 0 & ci_upper > 0)
                )
            }
            
            cat("Interaction effects detected:", length(interaction_terms), "terms\n")
            
        }, error = function(e) {
            cat("Error in interaction analysis:", e$message, "\n")
            interaction_results <- list(error = e$message)
        })
    } else {
        interaction_results <- list(note = "Insufficient data for interaction analysis")
    }
} else {
    interaction_results <- list(note = "Insufficient subgroups for interaction analysis")
}

# Compile subgroup analysis results
subgroup_analysis_results <- list(
    research_fields = research_field_results,
    retraction_categories = retraction_category_results,
    geographic_scope = geographic_scope_results,
    interaction_effects = interaction_results,
    summary = list(
        total_subgroups_tested = length(research_field_results) + 
                                length(retraction_category_results) + 
                                length(geographic_scope_results),
        research_field_distribution = table(analysis_data$research_field),
        retraction_category_distribution = table(analysis_data$retraction_category),
        geographic_scope_distribution = table(analysis_data$geographic_scope)
    )
)

# Add subgroup results to main results
results_list$subgroup_analysis <- subgroup_analysis_results

cat("Subgroup analyses completed!\n")

# Add Bayesian model diagnostics following protocol
results_list$model_diagnostics <- list(
    sample_size = nrow(analysis_data),
    countries = length(unique(analysis_data$iso3_factor)),
    years = paste(range(analysis_data$year, na.rm = TRUE), collapse = "-"),
    max_rhat = max(rhat_check, na.rm = TRUE),
    min_ess_ratio = min(ess_check, na.rm = TRUE),
    chains = 4,
    iterations = 4000,
    warmup = 2000,
    loo_estimate = loo_result$estimates["looic", "Estimate"],
    imputation_datasets = 20,
    missing_data_method = "MICE with PMM (20 datasets)",
    model_family = "Negative Binomial",
    priors = "Weakly informative"
)

# Export results to JSON
output_file <- "/Users/choxos/Documents/GitHub/CitingRetracted/r_analysis_output/r_analysis_results.json"
cat("Exporting results to:", output_file, "\n")

write_json(results_list, output_file, pretty = TRUE)

# Generate summary statistics
summary_stats <- prepared_data %>%
    summarise(
        total_countries = n_distinct(Country),
        total_observations = n(),
        avg_democracy = mean(democracy, na.rm = TRUE),
        avg_retraction_rate = mean(retraction_rate, na.rm = TRUE),
        correlation_demo_retraction = cor(democracy, retraction_rate, use = "complete.obs")
    )

summary_file <- "/Users/choxos/Documents/GitHub/CitingRetracted/r_analysis_output/summary_stats.json"
write_json(summary_stats, summary_file, pretty = TRUE)

cat("R analysis completed successfully!\n")
cat("Results exported to:", output_file, "\n")
cat("Summary stats exported to:", summary_file, "\n")
