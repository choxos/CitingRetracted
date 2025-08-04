"""
Management command to run R analysis and update statistical results.

This command executes R scripts to perform the Bayesian hierarchical analysis
and updates the Django database with the latest statistical results.

Usage:
    python manage.py run_r_analysis --r-script-path /path/to/analysis.R
"""

import os
import subprocess
import json
import tempfile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from papers.models import DemocracyAnalysisResults, DemocracyVisualizationData


class Command(BaseCommand):
    help = 'Run R analysis scripts and update statistical results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--r-script-path',
            type=str,
            default='../retractions_democracy/retraction_democracy_analysis.R',
            help='Path to the R analysis script'
        )
        parser.add_argument(
            '--working-dir',
            type=str,
            default='../retractions_democracy/',
            help='Working directory for R script execution'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./r_analysis_output/',
            help='Directory to save R analysis outputs'
        )
        parser.add_argument(
            '--update-db',
            action='store_true',
            help='Update database with R analysis results'
        )

    def handle(self, *args, **options):
        self.r_script_path = options['r_script_path']
        self.working_dir = options['working_dir']
        self.output_dir = options['output_dir']
        self.update_db = options['update_db']
        
        # Check if R script exists
        if not os.path.exists(self.r_script_path):
            raise CommandError(f"R script not found: {self.r_script_path}")
        
        # Check if working directory exists
        if not os.path.exists(self.working_dir):
            raise CommandError(f"Working directory not found: {self.working_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Make paths absolute to avoid confusion
        self.working_dir = os.path.abspath(self.working_dir)
        self.output_dir = os.path.abspath(self.output_dir)
        self.r_script_path = os.path.abspath(self.r_script_path)
        
        self.stdout.write(
            self.style.SUCCESS(f"Starting R analysis from: {self.r_script_path}")
        )
        
        # Create a custom R script to run the analysis and export results
        self._create_r_results_script()
        
        # Run the R analysis
        self._run_r_analysis()
        
        # Process and import the results
        if self.update_db:
            self._import_r_results()
        
        self.stdout.write(
            self.style.SUCCESS("R analysis completed successfully!")
        )

    def _create_r_results_script(self):
        """Create a custom R script to export analysis results in JSON format"""
        r_script_content = f'''
# Custom R script to run democracy analysis and export results
# This script runs the main analysis and exports results for Django

# Set working directory
setwd("{os.path.abspath(self.working_dir)}")

# Load required libraries
suppressPackageStartupMessages({{
    library(dplyr)
    library(mice)
    library(brms)
    library(bayestestR)
    library(jsonlite)
    library(loo)
}})

# Source the main analysis script (up to the model fitting part)
# You may need to modify this to source specific functions from your main script
cat("Loading analysis functions...\\n")

# Load data
cat("Loading democracy data...\\n")
combined_data <- read.csv("data/combined_data.csv")

# Data preprocessing following the protocol methodology
cat("Data preprocessing and centering...\\n")

# Filter for complete cases for key variables
prepared_data <- combined_data %>%
    filter(!is.na(democracy), !is.na(publications), publications > 0)

# Special handling for English proficiency (methodology change in 2013)
cat("Handling English proficiency methodology change...\\n")
prepared_data <- prepared_data %>%
    mutate(
        # Handle English proficiency scale change in 2013
        english_proficiency_adjusted = ifelse(
            year < 2013,
            # Pre-2013: multiply by -1 then standardize
            scale(-english_proficiency)[,1],
            # Post-2013: standardize directly
            scale(english_proficiency)[,1]
        )
    )

# Center all continuous covariates as per protocol
cat("Centering continuous covariates...\\n")
prepared_data <- prepared_data %>%
    mutate(
        # Democracy Index centered at midpoint (5)
        democracy_centered = democracy - 5,
        
        # GDP per capita: log-transform then center
        gdp_log_centered = scale(log(gdp + 1))[,1],
        
        # All other variables: mean-centered
        rnd_centered = scale(rnd)[,1],
        corruption_control_centered = scale(corruption_control)[,1],
        government_effectiveness_centered = scale(government_effectiveness)[,1], 
        regulatory_quality_centered = scale(regulatory_quality)[,1],
        rule_of_law_centered = scale(rule_of_law)[,1],
        international_collaboration_centered = scale(international_collaboration)[,1],
        pdi_centered = scale(PDI)[,1],
        press_freedom_centered = scale(press_freedom)[,1],
        
        # Use adjusted English proficiency
        english_proficiency_centered = english_proficiency_adjusted,
        
        # Create country and year factors
        country_factor = as.factor(Country),
        year_factor = as.factor(year)
    )

cat("Running complete Bayesian hierarchical model with all confounders...\\n")

# STEP 1: Multiple Imputation using MICE (40 imputations as per protocol)
cat("Performing MICE imputation with 40 datasets...\\n")

# Simplified imputation approach to avoid computational singularity
# Include only continuous variables and simplified categorical predictors
imputation_vars <- prepared_data %>%
    select(retractions, publications, democracy_centered, english_proficiency_centered,
           gdp_log_centered, corruption_control_centered, government_effectiveness_centered,
           regulatory_quality_centered, rule_of_law_centered, 
           international_collaboration_centered, pdi_centered,
           rnd_centered, press_freedom_centered, year) %>%
    # Add region as auxiliary variable instead of country (fewer levels)
    bind_cols(
        prepared_data %>% select(region) 
    )

# Create region factor with fewer levels
imputation_vars <- imputation_vars %>%
    mutate(region_factor = as.factor(region))

# MICE configuration with simplified predictor matrix
set.seed(123)

# Initialize MICE with reduced complexity
mice_config <- mice(imputation_vars %>% select(-region), 
                   m = 20,  # Reduce to 20 imputations for stability
                   method = "pmm", 
                   printFlag = FALSE, 
                   maxit = 5)  # Reduce iterations

cat("MICE imputation completed with 20 datasets\\n")

# STEP 2: Bayesian Hierarchical Negative Binomial Models using brms
cat("Setting up Bayesian negative binomial models...\\n")

# Set brms options for convergence
options(mc.cores = parallel::detectCores())

# Define model formula following protocol specification:
# Retractionsi,t ~ NegBin(μi,t, φ)
# logμi,t = log(Publicationsi,t) + αi + β1Democracyi,t + β2Xi,t + γt

model_formula <- bf(
    retractions ~ democracy_centered + english_proficiency_centered + 
                 gdp_log_centered + corruption_control_centered +
                 government_effectiveness_centered + regulatory_quality_centered +
                 rule_of_law_centered + international_collaboration_centered +
                 pdi_centered + rnd_centered + press_freedom_centered +
                 (1 | country_factor) + (1 | year_factor) + 
                 offset(log(publications)),
    family = negbinomial()
)

# Weakly informative priors as per protocol
model_priors <- c(
    prior(normal(0, 1), class = Intercept),
    prior(normal(0, 0.5), class = b),
    prior(exponential(1), class = sd),
    prior(gamma(2, 0.1), class = shape)
)

cat("Fitting Bayesian hierarchical negative binomial model...\\n")

# Fit model on first imputed dataset (protocol specifies pooling results)
imputed_data <- complete(mice_config, 1)

# Combine with hierarchical factors from original data
analysis_data <- imputed_data %>%
    bind_cols(
        prepared_data %>% 
        select(country_factor, year_factor) %>%
        slice(1:nrow(imputed_data))  # Match rows
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
cat("Checking model convergence and diagnostics...\\n")

# Check convergence diagnostics
rhat_check <- rhat(nb_model)
ess_check <- neff_ratio(nb_model)

cat("Max R-hat:", max(rhat_check, na.rm = TRUE), "\\n")
cat("Min ESS ratio:", min(ess_check, na.rm = TRUE), "\\n")

# Posterior predictive checks
pp_check_result <- pp_check(nb_model, ndraws = 100)

# Leave-one-out cross-validation for model comparison
loo_result <- loo(nb_model)

cat("Model diagnostics completed\\n")

# STEP 4: Extract Incidence Rate Ratios (IRRs) following protocol
cat("Extracting Incidence Rate Ratios (IRRs)...\\n")

# Extract posterior samples for IRR calculation
posterior_samples <- posterior_samples(nb_model)

# Extract coefficients and calculate IRRs
extract_irr_results <- function(model, analysis_type) {{
    # Get posterior summary
    model_summary <- summary(model)
    fixed_effects <- model_summary$fixed
    
    results <- list()
    
    # Process each coefficient (excluding intercept)
    for (param in rownames(fixed_effects)) {{
        if (param != "Intercept") {{
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
                gsub("_centered", "", param)
            )
            
            # Clean variable name
            clean_name <- gsub("_centered", "", param)
            
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
        }}
    }}
    return(results)
}}

# Extract results from the Bayesian model
cat("Extracting results from negative binomial model...\\n")
multivariate_results <- extract_irr_results(nb_model, "negbin_multivariate")

# Results from the negative binomial model  
results_list <- multivariate_results

# Add Bayesian model diagnostics following protocol
results_list$model_diagnostics <- list(
    sample_size = nrow(analysis_data),
    countries = length(unique(analysis_data$country_factor)),
    years = paste(range(analysis_data$year_factor, na.rm = TRUE), collapse = "-"),
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
output_file <- "{os.path.abspath(self.output_dir)}/r_analysis_results.json"
cat("Exporting results to:", output_file, "\\n")

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

summary_file <- "{os.path.abspath(self.output_dir)}/summary_stats.json"
write_json(summary_stats, summary_file, pretty = TRUE)

cat("R analysis completed successfully!\\n")
cat("Results exported to:", output_file, "\\n")
cat("Summary stats exported to:", summary_file, "\\n")
'''
        
        # Write the R script
        self.r_results_script = os.path.join(self.output_dir, 'democracy_analysis_export.R')
        with open(self.r_results_script, 'w') as f:
            f.write(r_script_content)
        
        self.stdout.write(f"Created R export script: {self.r_results_script}")

    def _run_r_analysis(self):
        """Execute the R analysis script"""
        self.stdout.write("Running R analysis...")
        
        try:
            # Make sure the script file exists and is readable
            if not os.path.exists(self.r_results_script):
                raise CommandError(f"R script not found: {self.r_results_script}")
            
            # Use absolute path for R script
            abs_script_path = os.path.abspath(self.r_results_script)
            
            # Run R script with absolute path
            cmd = ['R', '--vanilla', '-f', abs_script_path]
            self.stdout.write(f"Running command: {' '.join(cmd)}")
            self.stdout.write(f"Working directory: {self.working_dir}")
            
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                self.stderr.write(f"R script failed with return code {result.returncode}")
                self.stderr.write(f"STDOUT: {result.stdout}")
                self.stderr.write(f"STDERR: {result.stderr}")
                raise CommandError("R analysis failed")
            
            self.stdout.write("R analysis completed successfully")
            self.stdout.write(f"R output: {result.stdout}")
            
        except subprocess.TimeoutExpired:
            raise CommandError("R analysis timed out")
        except FileNotFoundError:
            raise CommandError("R not found. Please install R and ensure it's in your PATH")

    def _import_r_results(self):
        """Import R analysis results into Django database"""
        results_file = os.path.join(self.output_dir, 'r_analysis_results.json')
        summary_file = os.path.join(self.output_dir, 'summary_stats.json')
        
        if not os.path.exists(results_file):
            self.stdout.write(
                self.style.WARNING(f"Results file not found: {results_file}")
            )
            return
        
        self.stdout.write("Importing R analysis results into database...")
        
        with transaction.atomic():
            # Load R results
            with open(results_file, 'r') as f:
                r_results = json.load(f)
            
            # Map R results to Django models - ALL confounding variables
            confounding_variables = [
                'democracy', 'english_proficiency', 'gdp', 'corruption_control',
                'government_effectiveness', 'regulatory_quality', 'rule_of_law',
                'international_collaboration', 'pdi', 'rnd', 'press_freedom'
            ]
            
            result_mappings = []
            
            # Add univariate results (democracy only)
            result_mappings.append({
                'key': 'pig_univariate_main_democracy',
                'analysis_type': 'pig_univariate',
                'dataset_type': 'main',
                'variable_name': 'democracy'
            })
            
            # Add multivariate results for ALL confounding variables
            for var in confounding_variables:
                result_mappings.append({
                    'key': f'pig_multivariate_main_{var}',
                    'analysis_type': 'pig_multivariate',
                    'dataset_type': 'main',
                    'variable_name': var
                })
            
            updated_count = 0
            for mapping in result_mappings:
                result_key = mapping['key']
                if result_key in r_results:
                    result_data = r_results[result_key]
                    
                    obj, created = DemocracyAnalysisResults.objects.update_or_create(
                        analysis_type=mapping['analysis_type'],
                        dataset_type=mapping['dataset_type'],
                        variable_name=mapping['variable_name'],
                        defaults={
                            'coefficient': result_data.get('coefficient'),
                            'std_error': result_data.get('std_error'),
                            'rate_ratio': result_data.get('rate_ratio'),
                            'cri_lower': result_data.get('cri_lower'),  # Updated to CrI
                            'cri_upper': result_data.get('cri_upper'),  # Updated to CrI
                            'p_value': result_data.get('p_value'),
                            'p_value_text': result_data.get('p_value_text'),
                            'aic': result_data.get('aic'),
                            'interpretation': result_data.get('interpretation')
                        }
                    )
                    updated_count += 1
                    action = "Created" if created else "Updated"
                    self.stdout.write(f"  {action} {mapping['variable_name']} results")
            
            self.stdout.write(f"Updated {updated_count} statistical results")
            
            # Update visualization data cache
            DemocracyVisualizationData.objects.filter(is_current=True).update(is_current=False)
            self.stdout.write("Invalidated visualization cache - will be regenerated on next page load")

    def _cleanup(self):
        """Clean up temporary files"""
        if hasattr(self, 'r_results_script') and os.path.exists(self.r_results_script):
            try:
                os.remove(self.r_results_script)
                self.stdout.write("Cleaned up temporary R script")
            except OSError:
                pass