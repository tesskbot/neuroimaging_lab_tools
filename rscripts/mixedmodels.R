# Make set of mixed effects models

# Get the data
library(ggplot2)
library(pastecs)
library(reshape2)
library(gridExtra)
library(plyr)
library(xlsx)
library(corrplot)
library(ppcor)
library(lme4)
library(lattice)
library(bbmle)
library(lmerTest)
library(pbkrtest)
library(MASS)

#load("Workspace.RData")
#save.image("Workspace.RData")

#Set the location of the table containing longitudinal subject data
setwd("~/Dropbox/")
#Load the excel file
merge <- read.xlsx('.xls', 1)

merge$no <- as.numeric(merge$no)

#Filter for subjects with more than two timepoints
merge_3tp <- subset(merge, no>2)

#summarize by subject
merge_summary <- aggregate(merge, list(merge$B), mean)

#Do raw linear fit to longitudinal data for each subject
rawlm1 <- lmList(Factor1 ~ NP_YrsRelBL | BAC., data = merge_3tp, na.action=na.pass)
sl1 <- coef(rawlm1)

#Renames columns in slope output
renslopes = function(tbl, int, sl) {
  colnames(tbl)[1] <- int
  colnames(tbl)[2] <- sl
  return(tbl)
}

#rename columns
sl1 <- renslopes(sl1, "lmList_sl1", "lmList_int1")

# make rownames a column
sl1$BAC. <- rownames(sl1)

#insert slopes into factor tables
mergesl0 <- merge(merge_3tp, sl0, on="B")


#put all variables in the linear mixed effects model
lmer1 <- lmer(Factor1 ~ ss + ty*ss + nr*ss + go*ss + ya*ss + ll*ss + 
                sl*ss + fa*ss + (ss | B), data=merge_3tp)

#gets r-squared from the models
1-var(residuals(lmer0))/(var(model.response(model.frame(lmer0))))

#extract correlation matrices
#this tells us which variables are related to each other
cor_lmer = cov2cor(vcov(lmer1))

#summarize model outputs
summar = summary(lmer1)

#extract residuals
res_lmer <- residuals(lmer1)

#for plotting purposes
ploteffects(lmer1)