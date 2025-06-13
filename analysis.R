library(lme4)
library(sjPlot)
library(dplyr)
library(stargazer)
library(ggplot2)
library(wesanderson)
library(ggalt)
library(ggrepel)
library(patchwork)
library(ggpubr)

rates <- read.csv("rates.csv")
diversity <- read.csv("diversity.csv")

# Manipulation check
lm_model <- lm(eval_diversity ~ group, data = diversity)
summary(lm_model)

mean(rates_ran$y_for, na.rm = TRUE)
sd(rates_ran$y_for, na.rm = TRUE)
mean(rates_rec$y_for, na.rm = TRUE)
sd(rates_rec$y_for, na.rm = TRUE)

mean(rates_ran$y_fact, na.rm = TRUE)
sd(rates_ran$y_fact, na.rm = TRUE)
mean(rates_rec$y_fact, na.rm = TRUE)
sd(rates_rec$y_fact, na.rm = TRUE)

# Level of serendipity seeking
diversity <- diversity %>%
  mutate(
    gender = recode(gender, 'niet-binair/anders' = 'other', 'wil ik niet zeggen' = 'other'),
    gender = case_when(
      gender == "vrouw" ~ "woman",
      TRUE ~ gender  # Keep other values unchanged
    ),
    gender = factor(gender) %>% relevel(ref = "other"),
    polefficacy = (polefficacy1 + polefficacy2) / 2)  %>%
  mutate_at(vars(education, newsinterest, polinterest, polefficacy), as.numeric)
diversity$group <- factor(diversity$group)

# Randomization checks
# Gender
# Exclude "other" from the gender column
diversity_filtered <- diversity[diversity$gender %in% c("woman", "man"), ]
# Create binary gender variable: 1 = woman, 0 = man
diversity_filtered$gender_numeric <- ifelse(diversity_filtered$gender == "woman", 1, 0)
# Run logistic regression
glm_gender_model <- glm(gender_numeric ~ group, family = binomial, data = diversity_filtered)
# View summary
summary(glm_gender_model)

# Define the variables for randomization checks
variables <- c("age", "education", "newsinterest", "polorient", "polinterest", "polefficacy")
# Loop through each variable and run a linear regression model against the group
for (var in variables) {
  formula <- as.formula(paste(var, "~ group"))
  lm_model <- lm(formula, data = diversity)
  print(summary(lm_model))
}

## Stats
mean(diversity$age, na.rm = TRUE)
sd(diversity$age, na.rm = TRUE)

diversity %>%
  count(gender) %>% 
  mutate(percent = n / sum(n) * 100)

diversity %>%
  count(education) %>% 
  mutate(percent = n / sum(n) * 100)

mean(diversity$newsinterest, na.rm = TRUE)
sd(diversity$newsinterest, na.rm = TRUE)

diversity %>%
  count(group) %>% 
  mutate(percent = n / sum(n) * 100)

mean(diversity$ratio, na.rm = TRUE)
sd(diversity$ratio, na.rm = TRUE)

mean(diversity$eval_diversity, na.rm = TRUE)
sd(diversity$eval_diversity, na.rm = TRUE)

# Models
lm_model <- lm(ratio ~ group, data = diversity)
summary(lm_model)

lm_models <- lm(ratio ~ group + newsinterest + age + gender + education + polorient + polinterest + polefficacy, 
               data = diversity)
summary(lm_models)

# Create prediction dataframe
pred_df <- data.frame(group = unique(diversity$group)) %>%
  arrange(group)

# Add predicted values and confidence intervals
pred_out <- predict(lm_model, newdata = pred_df, interval = "confidence")
pred_df <- cbind(pred_df, pred_out)

# Plot with points and error bars
ggplot(diversity, aes(x = group, y = ratio)) +
  geom_jitter(width = 0.2, alpha = 0.5, color = "#899DA4") +  # Raw scatter
  geom_point(data = pred_df, aes(x = group, y = fit),
             color = "#C93312", shape = 8, size = 3, inherit.aes = FALSE) +  # Predicted means
  geom_errorbar(data = pred_df, aes(x = group, ymin = lwr, ymax = upr), 
                width = 0.15, color = "#C93312", inherit.aes = FALSE) +  # 95% CI bars
  labs(
    title = "Predicted values of serendipity seeking",
    x = "", y = "Serendipity seeking"
  ) +
  scale_x_discrete(labels = c("Random group", "Personalized group")) +
  theme_minimal(base_family = "Times New Roman") + 
  theme(
    plot.title = element_text(size = 20, family = "Times New Roman", face = "bold"),
    axis.title = element_text(size = 18, family = "Times New Roman", face = "bold"),
    axis.text = element_text(size = 14, family = "Times New Roman", face = "bold"),
    legend.text = element_text(size = 14, family = "Times New Roman", face = "bold"),
    legend.title = element_text(size = 14, face = "bold", family = "Times New Roman"),
    legend.position = "bottom",
    legend.spacing.x = unit(0.5, 'cm')
  )

# Ratings
rates <- rates %>%
  mutate(
    across(c(group, recommended, mystery), as.factor),
    gender = recode(gender, 'niet-binair/anders' = 'other', 'wil ik niet zeggen' = 'other'),
    gender = case_when(
      gender == "vrouw" ~ "woman",
      TRUE ~ gender  # Keep other values unchanged
    ),
    gender = factor(gender) %>% relevel(ref = "other"),
    polefficacy = (polefficacy1 + polefficacy2) / 2)  %>%
    mutate_at(vars(education, newsinterest, polinterest, polefficacy), as.numeric)

# Models
rates_ran <- subset(rates, group == 0)
rates_rec <- subset(rates, group == 1)

outcome_vars <- c("rating", "rating2")
predictor_vars <- c("y_for", "y_fact")
modelss <- list()

for (outcome in outcome_vars) {
  for (predictor in predictor_vars) {
    # Basic models
    formula_basic <- as.formula(paste(outcome, "~", predictor, "+ mystery + (1 +", predictor, "| user_id)"))
    modelss[[paste0("model_", outcome, "_", predictor)]] <- lmer(formula_basic, data = rates_ran)
  }
}

tab_model(modelss,
          show.ci = FALSE, p.style = 'stars')
stargazer(modelss,
          title = "RQ2 mystery box", align = TRUE,
          digits = 2,
          star.cutoffs = c(0.05, 0.01, 0.001))



















