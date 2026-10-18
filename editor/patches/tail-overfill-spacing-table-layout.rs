// ==== find ====
                            hit_hard_break = true;
                            break;
                        }
                    }
                    let visible_tail_before_spacer = relaxed_hard_break
                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height);
// ==== replace ====
                            hit_hard_break = true;
                            break;
                        }
                    }
                    let visible_tail_before_spacer = relaxed_hard_break
                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height)
                        // [claude-hwpx tail-overfill-spacing] 넘침은 그 줄의 줄 간격까지만(HWPX). 단위 높이 전체를 허용해 d087 의 171px 그림 줄이 135px 넘쳤다
                        && (!self.profile.get().hwpx_container()
                            || h + u.height - avail_height
                                <= cell
                                    .paragraphs
                                    .get(u.para_idx)
                                    .and_then(|p| p.line_segs.get(u.vis_start))
                                    .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))
                                    .unwrap_or(u.height)
                                    + 0.5);
// ==== next ====
avail_height, over
                            );
                        }
                    }
                    let visible_tail_before_spacer = relaxed_hard_break
                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height);
// ==== replace ====
avail_height, over
                            );
                        }
                    }
                    let visible_tail_before_spacer = relaxed_hard_break
                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height)
                        // [claude-hwpx tail-overfill-spacing] 넘침은 그 줄의 줄 간격까지만(HWPX). 단위 높이 전체를 허용해 d087 의 171px 그림 줄이 135px 넘쳤다
                        && (!self.profile.get().hwpx_container()
                            || h + u.height - avail_height
                                <= cell
                                    .paragraphs
                                    .get(u.para_idx)
                                    .and_then(|p| p.line_segs.get(u.vis_start))
                                    .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))
                                    .unwrap_or(u.height)
                                    + 0.5);
