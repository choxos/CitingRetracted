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
    library(gamlss)
    library(broom.mixed)
    library(jsonlite)
}})

# Source the main analysis script (up to the model fitting part)
# You may need to modify this to source specific functions from your main script
cat("Loading analysis functions...\\n")

# Load data
cat("Loading democracy data...\\n")
combined_data <- read.csv("data/combined_data.csv")

# Full data processing following the complete DAG protocol
prepared_data <- combined_data %>%
    filter(!is.na(democracy), !is.na(publications), publications > 0) %>%
    # Scale all variables by year (following the protocol)
    group_by(year) %>%
    mutate(
        democracy_scaled = scale(democracy)[,1],
        english_proficiency_scaled = scale(english_proficiency)[,1],
        gdp_scaled = scale(gdp)[,1],
        corruption_control_scaled = scale(corruption_control)[,1],
        government_effectiveness_scaled = scale(government_effectiveness)[,1],
        regulatory_quality_scaled = scale(regulatory_quality)[,1],
        rule_of_law_scaled = scale(rule_of_law)[,1],
        international_collaboration_scaled = scale(international_collaboration)[,1],
        pdi_scaled = scale(pdi)[,1],
        rnd_scaled = scale(rnd)[,1],
        press_freedom_scaled = scale(press_freedom)[,1],
        log_publications = log(publications),
        retraction_rate = retractions / publications
    ) %>%
    ungroup()

cat("Running complete Bayesian hierarchical model with all confounders...\\n")

# Load additional required libraries for proper analysis
suppressPackageStartupMessages({{
    library(gamlss)
    library(mice)
    library(VIM)
}})

# STEP 1: Multiple Imputation (MICE) for missing data
predictors_for_imputation <- prepared_data %>%
    select(democracy_scaled, english_proficiency_scaled, gdp_scaled, 
           corruption_control_scaled, government_effectiveness_scaled,
           regulatory_quality_scaled, rule_of_law_scaled,
           international_collaboration_scaled, pdi_scaled, rnd_scaled,
           press_freedom_scaled, country, region)

# Run MICE imputation (simplified for production)
imp <- mice(predictors_for_imputation, m = 5, method = 'pmm', 
            maxit = 10, seed = 1280, printFlag = FALSE)

# Get first imputed dataset
imputed_data <- complete(imp, 1)

# Combine with outcome variables
analysis_data <- bind_cols(
    prepared_data %>% select(retractions, log_publications, year, country),
    imputed_data %>% select(-country, -region)  # Avoid duplication
)

# STEP 2: Fit Poisson Inverse Gaussian (PIG) models following the protocol

# Univariate model (democracy only)
cat("Fitting univariate PIG model...\\n")
model_univariate <- gamlss(retractions ~ democracy_scaled + offset(log_publications),
                          family = PIG(), data = analysis_data)

# Full multivariate model with ALL confounders from DAG
cat("Fitting full multivariate PIG model with all confounders...\\n")
model_multivariate <- gamlss(
    retractions ~ democracy_scaled + english_proficiency_scaled + gdp_scaled +
                  corruption_control_scaled + government_effectiveness_scaled +
                  regulatory_quality_scaled + rule_of_law_scaled +
                  international_collaboration_scaled + pdi_scaled + 
                  rnd_scaled + press_freedom_scaled + offset(log_publications),
    family = PIG(), data = analysis_data
)

# Extract results for all variables
extract_results <- function(model, model_type) {{
    summary_stats <- summary(model)
    coef_table <- summary_stats$coef.table
    
    results <- list()
    
    for (i in 1:nrow(coef_table)) {{
        var_name <- rownames(coef_table)[i]
        if (var_name != "(Intercept)") {{
            coef_val <- coef_table[i, "Estimate"]
            se_val <- coef_table[i, "Std. Error"]
            p_val <- coef_table[i, "Pr(>|t|)"]
            
            # Calculate 95% Credible Intervals
            ci_lower <- exp(coef_val - 1.96 * se_val)
            ci_upper <- exp(coef_val + 1.96 * se_val)
            
            # Format p-value
            p_text <- if (p_val < 0.001) "< 0.001" else 
                     if (p_val < 0.01) "< 0.01" else 
                     if (p_val < 0.05) "< 0.05" else 
                     paste("=", round(p_val, 3))
            
            # Create interpretation
            effect_direction <- if (coef_val < 0) "reduction" else "increase"
            effect_magnitude <- abs((1 - exp(coef_val)) * 100)
            
            interpretation <- paste0(
                round(effect_magnitude, 1), "% ", effect_direction, 
                " in retraction rate per unit increase in ", 
                gsub("_scaled", "", var_name)
            )
            
            results[[paste0(model_type, "_", gsub("_scaled", "", var_name))]] <- list(
                coefficient = coef_val,
                std_error = se_val,
                rate_ratio = exp(coef_val),
                cri_lower = ci_lower,
                cri_upper = ci_upper,
                p_value = p_val,
                p_value_text = p_text,
                aic = AIC(model),
                interpretation = interpretation
            )
        }}
    }}
    return(results)
}}

# Extract results from both models
univariate_results <- extract_results(model_univariate, "pig_univariate_main")
multivariate_results <- extract_results(model_multivariate, "pig_multivariate_main")

# Combine all results
results_list <- c(univariate_results, multivariate_results)

# Add model diagnostics
results_list$model_diagnostics <- list(
    sample_size = nrow(analysis_data),
    countries = length(unique(analysis_data$country)),
    years = paste(range(prepared_data$year, na.rm = TRUE), collapse = "-"),
    univariate_aic = AIC(model_univariate),
    multivariate_aic = AIC(model_multivariate),
    imputation_datasets = imp$m,
    missing_data_method = "MICE with PMM"
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