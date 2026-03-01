            # 🔥 【100%確実版】SBI証券のWebサイト注文ページへ飛ばす！
            # 銘柄詳細ページへダイレクトにジャンプするリンクだよ
            sbi_web_link = f"https://site0.sbisec.co.jp/ETGate/?_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataAreaID=W6&_ActionID=DefaultAID&get_corp_info=dom&cat1=market&cat2=none&art_code={search_us}&i_stock_code={search_us}&i_exchange_code=UST"
            
            st.markdown(f'''
                <a href="{sbi_web_link}" target="_blank">
                    <button style="
                        width:100%; 
                        padding:18px; 
                        background:#400080; 
                        color:white; 
                        border-radius:12px; 
                        font-weight:bold; 
                        border:2px solid #ff00ff;
                        box-shadow: 0 0 15px #ff00ff;
                        cursor:pointer;">
                        SBI証券で {search_us} を注文する 🦅💥
                    </button>
                </a>
                ''', unsafe_allow_html=True)
