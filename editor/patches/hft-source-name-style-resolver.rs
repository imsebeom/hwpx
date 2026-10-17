// ==== find ====
            decision.css_family_chain.push(resolved.clone());
// ==== replace ====
            // [claude-hwpx hft-source-name] 대체되는 글꼴이라도 원래 이름으로 폭 표(한/글 실측)가 등록돼 있으면 원래 이름을 앞에 둔다.
            // 폭은 첫 이름으로 재고, 그리기는 브라우저에 없는 원래 이름을 건너뛰어 대체 글꼴로 한다.
            if substitution.is_some()
                && resolved != *name
                && crate::renderer::font_metrics_data::claude_runtime_has_metric(name)
            {
                decision.css_family_chain.push(name.clone());
            }
            decision.css_family_chain.push(resolved.clone());
