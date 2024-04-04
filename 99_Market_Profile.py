!pip install MarketProfile
!pip install git+https://github.com/baselsm/tvdatafeed
!pip install scipy
!pip install matplotlib
!pip install mplcyberpunk
!pip install mplfinance
!pip install vectorbt
import pandas as pd
from urllib import request
import ssl
from tvDatafeed import TvDatafeed, Interval
from market_profile import MarketProfile
import matplotlib.pyplot as plt
import mplfinance as mpf
import mplcyberpunk
import vectorbt as vbt
tv = TvDatafeed()

def Hisse_Temel_Veriler():
    url1="https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx#page-1"
    context = ssl._create_unverified_context()
    response = request.urlopen(url1, context=context)
    url1 = response.read()
    df = pd.read_html(url1,decimal=',', thousands='.')                         #Tüm Hisselerin Tablolarını Aktar
    df=df[6]
    Hisseler=df['Kod'].values.tolist()
    return Hisseler

def calculate_market_profile(subset_data):
    mp = MarketProfile(subset_data)
    mp_slice = mp[data.index.min():data.index.max()]
    POC = mp_slice.poc_price
    VAL, VAH = mp_slice.value_area
    return VAH, VAL, POC


def Plot_Candle(Hisse,data):
    df=data.tail(45).copy()
    plt.close()
    df.reset_index(drop=True, inplace=True)
    df.set_index('datetime', inplace=True)

    with plt.style.context('cyberpunk'):
        fig, axs = plt.subplots(2, sharex=True, height_ratios=[6, 1])
        fig.suptitle(Hisse+' Market Profile',style='italic',fontsize=16,fontweight="bold")
        mco = [None] * len(df)
        # Plotting VAH, POC, and VAL with specific colors
        add1 = mpf.make_addplot(df['VAH'], ax=axs[0], color='b', title='VAH')
        add2 = mpf.make_addplot(df['POC'], ax=axs[0], color='r', title='POC')
        add3 = mpf.make_addplot(df['VAL'], ax=axs[0], color='g', title='VAL')
        axs[1].set_title('Volume')
        mpf.plot(df, volume=axs[1], type='candle', style='charles', ax=axs[0], addplot=[add1,add2,add3])
    
    plt.gcf().set_size_inches(16, 9)  # Set the figure size
    plt.savefig(Hisse+' Market Profile.png', format='png', dpi=300)
    return

Titles=['Hisse Adı','Toplam Bakılan Bar Sayısı',
        'Al ve Tut Getirisi','Algoritma Getirisi',
        'Kazanma Oranı[%]','Sharpe Oranı',
        'Ort. Kazanma Oranı [%]','Ort Kazanma Süresi',
        'Ort. Kayıp Oranı [%]','Ort Kayıp Süresi',
        'Giriş Sinyali','Çıkış Sinyali']

df_signals=pd.DataFrame(columns=Titles)

Hisseler=Hisse_Temel_Veriler()

for j in range(0, len(Hisseler)):
    print(Hisseler[j])
    try:
        data = tv.get_hist(symbol=Hisseler[j], exchange='BIST', interval=Interval.in_1_hour, n_bars=5000)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()

        data['VAL'] = 0
        data['VAH'] = 0
        data['POC'] = 0

        n_bars = 45
        for i in range(0, len(data), n_bars):
            subset_data = data.iloc[i:i + n_bars]
            VAH, VAL, POC = calculate_market_profile(subset_data)
            data.loc[i:i + n_bars - 1, 'VAH'] = float(VAH)
            data.loc[i:i + n_bars - 1, 'VAL'] = float(VAL)
            data.loc[i:i + n_bars - 1, 'POC'] = float(POC)

        data['Entry']=data['Close']<data['VAL']
        data['Exit']=data['Close']>data['VAL']
        psettings = {'init_cash': 100,'freq': 'H', 'direction': 'longonly', 'accumulate': True}
        pf = vbt.Portfolio.from_signals(data['Close'], entries=data['Entry'], exits=data['Exit'],**psettings)
        Stats=pf.stats()
        print(Stats)

        Buy=False
        Sell=False
        Signals = data.tail(2)
        Signals = Signals.reset_index()
        Buy = Signals.loc[0, 'Entry'] == False and Signals.loc[1, 'Entry'] ==True
        Sell = Signals.loc[0, 'Exit'] == False and Signals.loc[1, 'Exit'] == True


        L1 = [Hisseler[j], len(data),
            round(Stats.loc['Benchmark Return [%]'], 2),round(Stats.loc['Total Return [%]'], 2),
            round(Stats.loc['Win Rate [%]'], 2),round(Stats.loc['Sharpe Ratio'], 2),
            round(Stats.loc['Avg Winning Trade [%]'], 2),str(Stats.loc['Avg Winning Trade Duration']),
            round(Stats.loc['Avg Losing Trade [%]'], 2),str(Stats.loc['Avg Losing Trade Duration']),
            str(Buy), str(Sell)]

        print(L1)
        df_signals.loc[len(df_signals)] = L1
    except:
        pass
