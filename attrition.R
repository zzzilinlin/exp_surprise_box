library(dplyr)

attrition <- read.csv("userinfo_attrition.csv")

# distribution of usage
sum(attrition$date > 1)
sum(attrition$date > 3)
sum(attrition$date > 5)
sum(attrition$date >= 7)

# create the 'included' column - more than 5 days
attrition$included <- ifelse(attrition$date > 5, 1, 0)

# calculate the distribution
table(attrition$included)

# clean up the df
attrition <- attrition %>%
  mutate(
    gender = recode(gender, 'niet-binair/anders' = 'other', 'wil ik niet zeggen' = 'other'),
    gender = case_when(
      gender == "vrouw" ~ "woman",
      TRUE ~ gender
    ),
    gender = factor(gender) %>% relevel(ref = "other"),
    polefficacy = (polefficacy1 + polefficacy2) / 2)  %>%
  mutate_at(vars(education, newsinterest, polinterest, polefficacy), as.numeric)
attrition$group <- factor(attrition$group)
attrition$included <- factor(attrition$included)

# exp group
table(attrition$included, attrition$group)
chisq.test(table(attrition$included, attrition$group))
fisher.test(table(attrition$included, attrition$group))

# gender
table(attrition$included, attrition$gender)
chisq.test(table(attrition$included, attrition$gender))
fisher.test(table(attrition$included, attrition$gender))

# edu
by(attrition$education, attrition$included, summary)
t.test(education ~ included, data = attrition)

# age
by(attrition$age, attrition$included, summary)
t.test(age ~ included, data = attrition)

# other pol ones
by(attrition$polorient, attrition$included, summary)
by(attrition$newsinterest, attrition$included, summary)
by(attrition$polinterest, attrition$included, summary)
by(attrition$polefficacy, attrition$included, summary)

t.test(polorient ~ included, data = attrition)
t.test(newsinterest ~ included, data = attrition)
t.test(polinterest ~ included, data = attrition)
t.test(polefficacy ~ included, data = attrition)

# boxplot
boxplot(polorient ~ included, data = attrition,
        main = "Political orientation by inclusion status",
        xlab = "Included", ylab = "Political Orientation")

# stats
attrition$polorient_cat <- cut(attrition$polorient,
                               breaks = c(-Inf, -0.0001, 0.0001, Inf),
                               labels = c("negative", "neutral", "positive"))
table(attrition$included, attrition$polorient_cat)

