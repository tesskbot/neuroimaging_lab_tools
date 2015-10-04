ploteffects <- function(lmer_out) {
  # Plot the magnitude of the fixed effects in an lmer model
  #
  # Args:
  #  lmer_out: output of lmer
  #
  
  #extract only the fixed effects data from the lmer object
  fixef_out <- data.frame(fixef(lmer_out))
  names(fixef_out)[1] <- "slope"
  fixef_out$label <- row.names(fixef_out)
  fixef_out <- fixef_out[-1,]
  fixef_out_sorted <- fixef_out[order(fixef_out$slope), ]
  numlabs <- dim(fixef_out_sorted)
  numlabs <- numlabs[1]
  
  #plot
  par(mar=c(15,8,1,1))
  plot(fixef_out_sorted$slope, xaxt="n")
  abline(a=0, b=0, col='red')
  axis(1, at=1:numlabs, labels=fixef_out_sorted$label, las=3)
}