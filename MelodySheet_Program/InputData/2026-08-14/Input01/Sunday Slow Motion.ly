\version "2.24.4"

\language "english"

#(define fonts
   (make-pango-font-tree "Noto Sans CJK KR" "Noto Sans CJK KR" "Noto Sans CJK KR" 1.0)
)

\header {
  title = "Sunday Slow Motion"
  subtitle = ""
  composer = "Kim Sanghoon"
}

\paper {
  #(set-default-paper-size "a4")
  top-margin = 15
  bottom-margin = 20
  left-margin = 10
  right-margin = 10
  oddFooterMarkup = \markup {
    \column {
      \fill-line {
        \general-align #Y #2.5 {
          
        }
      }
      \vspace #1
      \fill-line { \fontsize #-2 "Made with ❤ using klangio!" }
    }
  }
}

ChordsPartZeroStaffZero = \chordmode {
  s8 s8 bf8:m7 s8 s4 s4 |
  ef8: s8 s8 s8 s2 |
  s1 |
  s1 |
  s8 s8 s8 s8 s4 s4 |
  ef8: s8 \tuplet 3/2 { s8 s4 }s2 |
  s1 |
  bf8: s8 s8 s8 s4 s4 |
  ef4: s16 s8. s2 |
  s1 |
  g8:m s8 s8 s8 s4 s4 |
  f4: f8: s8 s8 s8 f4: |
  s1 |
  g4:m s8 s8 s4 s4 |
  ef1: |
  g1:m |
  s4 d2.:m |
  ef16: s8. s4 s4 s16 s8 s16 |
  s2 c8:m s8 ef8: s8 |
  s4 s4 f4:7 c8:m s8 |
  g8:m s8 s8 s8 s2 |
  bf4: g8:m s8 s4 f4: |
  s8. s16 bf4: s4 s8. s16 |
  s8 s8 s8 s8 s8 s8 s8 s8 |
  s8 s8 g8:m s8 s4 s8 s8 |
  s4 s4 d4:m s8 s8 |
  ef1: |
  s2. g8:m s8 |
  s4 d2.:m |
  ef8: s8 s4 s4 s8 s8 |
  s2 f8:7 s8 ef8: s8 |
  s4 f4:7 s4 s8 s8 |
  g8.:m s16 s16 s8. s2 |
  bf4: g8:m7 s8 s4 f4: |
  s8. s16 bf4: s4 s8. s16 |
  s8 s8 s8 s8 s8 s8 s8 s8 |
  s4 d8:m7 s8 ef4: s4 |
  s2. s8. s16 |
  f4:7 f8: s8 bf2: |
  s2 s8 s8 ef8: s8 |
  s4 s2. |
  g4:m s16 s8. s16 s16 s16 s16 bf16: s8 s16 |
  ef4: s8 s16 s16 s8 s16 s16 s8 s16 s16 |
  f4: s8 s16 s16 f8:7 s8 f4: |
  s4 bf16: s16 s16 s16 s16 s16 s16 s16 s16 s16 s16 s16 |
  s16 s16 s16 s16 bf16: s16 s16 s16 bf16: s16 s16 s16 s16 s16 s16 s16 |
  ef4: g16:m s16 s16 s16 s16 s16 s16 s16 d16:m s16 s16 s16 |
  \tuplet 3/2 { ef8: s8 s8 }s16 s16 s16 s16 s4 d16:m s16 s16 s16 |
  ef16: s16 s16 s16 s16 s16 s16 s16 s16 s16 s16 s16 d16:m s16 s16 s16 |
  f8: s8 s8 s8 s16 s16 s8 \tuplet 3/2 { s8 s8 s8 }|
  s1 |
  bf8: s8 s8 s8 s8 s8 s8 s8 |
  s8 s8 s8 s8 s8 s8 ef8: s8 |
  s4 s8 s8 s8 s8 s8 s8 |
  s4 s8 s8 s8 s8 g8:m s8 |
  s4 s8 s8 s4 f8: s8 |
  ef2: s2 |
  s4 s4 s4 d4:m |
  bf4: ef4: s2 |
  s4 s2 bf4: |
  f1: |
  s2. s8 s8 |
  s16 s8. s4 s16 s8. g8:m s8 |
  s4 s2 s4 |
  d4:m ef8: s8 s2 |
  s4 s2 s8 s8 |
  g4:m s2 s4 |
  d4:m ef8: s8 s2 |
  s1 |
  s8 s8 s8 s8 s8 s8 af4: |
  s8 s8 g4:m7 g4:m s8 s16 g16:m7 |
  s4 s8 s8 s4 s8 s8 |
  s8. s16 f4: s4 s8. s16 |
  g2:m7 s2 |
  s4 bf8: s8 s4 ef8: s8 |
  s2 s2 |
  s4 s8 s8 bf4: s8 s8 |
  s1 |
  f2: s8 s8 s4 |
  s1 |
  bf8: s8 bf8: s8 s4 ef4: |
  s8 s8 s8 s8 s2 |
  s1 |
  g8.:m s16 s16 s8 s16 s16 s8. bf16: s8. |
  s16 s8. f8.: s16 s4 s8. s16 |
  s1 |
  bf1: |
  s4 s4 s8 s8 s4 |
  s1 |
  s1 |
}

NotesPartZeroStaffZero = {
  \clef "treble"
  \numericTimeSignature \time 4/4
  \key bf \major
  \set fingeringOrientations = #'(down)
  \tempo 4 = 115
  <bf'>8 <f''>8 <bf''>8 <c'''>8 <f'''>4 <bf''>4 | % 1
  <bf'>8 <bf'>8 <f''>8 <g'' ef'>8 <bf''>2 ~  | % 2
  <bf''>1 ~  | % 3
  <bf''>1 | % 4
  <bf'>8 <f''>8 <bf''>8 <c'''>8 <f'''>4 <bf''>4 | % 5
  <ef'>8 <bf'>8 \tuplet 3/2 { <f''>8 <g''>4 }<bf''>2 | % 6
  r1 | % 7
  r8 <f'>8 <bf'>8 <c''>8 <f''>4 <bf'>4 | % 8
  r4 <g'>16 <bf'>8. <f''>2 | % 9
  r1 | % 10
  r8 <d'>8 <g'>8 <bf'>8 <d''>4 <bf'>4 | % 11
  <f'>4 <bf'>8 <c''>8 ~  <c''>8 <f'>8 ~  <f'>4 ~  | % 12
  <f'>1 | % 13
  r4 <g'>8 <a'>8 <bf'>4 <d'>4 ~  | % 14
  <d'>1 | % 15
  r1 | % 16
  <bf'>4 <d''>2. | % 17
  r16 <bf'>8. ~  <bf'>4 ~  <bf'>4 ~  <bf'>16 <g'>8 <bf'>16 | % 18
  <ef''>2 <ef''>8 <g'>8 <a'>8 <bf'>8 | % 19
  <d'' ef'>4 <bf'>4 <c''>4 ~  <c''>8 <d'>8 | % 20
  <d'>8 <d'>8 <g'>8 <bf'>8 <d''>2 | % 21
  r4 <g' d'>8 <f'>8 <f' bf'>4 <d'>4 | % 22
  r8. <f'>16 ~  <f'>4 ~  <f'>4 ~  <f'>8. <d'>16 | % 23
  <f'>8 <bf'>8 <f'>8 <d'>8 ~  <d'>8 <d'>8 <f'>8 <bf'>8 | % 24
  <f'>8 <d'>8 <f' bf'>8 <d'>8 <bf'>4 ~  <bf'>8 <a'>8 | % 25
  <bf'>4 <d'' d'>4 <f' a' d'>4 ~  <f' a' d'>8 <g'>8 | % 26
  <g'>1 | % 27
  r2. <g'>8 <a'>8 | % 28
  <bf'>4 <bf' d'' d'>2. | % 29
  <g'>8 <ef'>8 ~  <ef'>4 <ef'>4 <ef'>8 <bf'>8 ~  | % 30
  <bf'>2 <ef''>8 <g'>8 <a'>8 <bf'>8 | % 31
  <d''>4 <bf'>4 <c''>4 <a'>8 <d''>8 | % 32
  <d''>8. <d'>16 ~  <d'>16 <g'>8. <bf'>2 | % 33
  r4 <g' d'>8 <f' a'>8 <bf'>4 <d'>4 | % 34
  r8. <f'>16 ~  <f'>4 ~  <f'>4 ~  <f'>8. <d'>16 | % 35
  <f'>8 <bf'>8 <f'>8 <d'>8 ~  <d'>8 <d'>8 <f'>8 <bf'>8 | % 36
  <f''>4 ~  <f''>8 <d'>8 ~  <d'>4 <ef'>4 | % 37
  <ef'>2. <a'>8. <c''>16 | % 38
  <ef'>4 ~  <ef'>8 <d'>8 <d'' d'>2 ~  | % 39
  \tempo 4 = 68
  <d'' d'>2 <d'>8 <f''>8 ~  <f''>8 <d''>8 | % 40
  r4 <d'>2. | % 41
  r4 <d'>16 <g'>8. ~  <g'>16 <d'>16 <bf'>16 <d''>16 ~  <d''>16 <f'>8 <bf'>16 | % 42
  <g' bf'>4 ~  <g' bf'>8 <ef'>16 <bf'>16 <ef'>8 <ef'>16 <bf'>16 <d'' ef'>8 <ef'>16 <bf'>16 | % 43
  <bf'>4 <ef'>8 <ef'>16 <bf'>16 <a'>8 <f'>8 ~  <f'>4 ~  | % 44
  <f'>4 <bf'>16 <d''>16 <f''>16 <bf''>16 <bf'>16 <d''>16 <f''>16 <bf''>16 <bf'>16 <d''>16 <f''>16 <bf''>16 | % 45
  <bf'>16 <d''>16 <f''>16 <bf''>16 <bf'' bf' ef'>16 <d''>16 <f''>16 <bf''>16 <bf'>16 <d''>16 <f''>16 <bf''>16 <bf'>16 <d''>16 <f''>16 <bf''>16 | % 46
  <bf' f'' bf'' f''' d'>4 <bf''>16 <bf'>16 <d''>16 <bf''>16 <g'>16 <bf'>16 <d''>16 <bf''>16 <a'' f'>16 <a'>16 <d''>16 <a''>16 | % 47
  \tuplet 3/2 { <g''>8 <g'>8 <bf'>8 }<ef''>16 <ef'>16 <g'>16 <bf'>16 <ef''>4 <f''>16 <f'>16 <bf'>16 <f''>16 | % 48
  <d''>16 <g'>16 <bf'>16 <d''>16 <ef'>16 <g'>16 <bf'>16 <d''>16 <ef'>16 <g'>16 <bf'>16 <d''>16 <f''>16 <f'>16 <bf'>16 <f''>16 | % 49
  \tempo 4 = 100
  <c''>8 <f'>8 <bf'>8 <c''>8 ~  <c''>16 <f'>16 <bf'>8 \tuplet 3/2 { <c''>8 <a'>8 <f'>8 ~  }| % 50
  <f'>1 | % 51
  r8 <d'>8 <f'>8 <bf'>8 ~  <bf'>8 <d'>8 <f'>8 <bf'>8 ~  | % 52
  <bf'>8 <d'>8 <f'>8 <bf'>8 ~  <bf'>8 <d'>8 <f'>8 <bf'>8 | % 53
  r4 <f'>8 <bf'>8 ~  <bf'>8 <ef'>8 <f'>8 <bf'>8 ~  | % 54
  <bf'>4 <f'>8 <bf'>8 <c''>8 <ef'>8 <f'>8 <bf'>8 | % 55
  <bf'>4 ~  <bf'>8 <bf'>8 ~  <bf'>4 <d'>8 <bf'>8 | % 56
  <a'>2 <g'>2 ~  | % 57
  <g'>4 <ef'>4 <g' ef'>4 <ef'>4 | % 58
  <f'>4 <d'>4 <ef'>2 ~  | % 59
  <ef'>4 <ef'>2 <ef'>4 | % 60
  \tempo 4 = 136
  r1 | % 61
  r2. <bf'>8 <a'>8 ~  | % 62
  <a'>16 <f'>8. ~  <f'>4 ~  <f'>16 <f'>8. <a'>8 <f''>8 | % 63
  <d'' bf'>4 <g'>2 <d'>4 | % 64
  <d''>4 ~  <d''>8 <bf'>8 <g' ef'>2 | % 65
  <ef'>4 <ef'>2 <ef'>8 <bf'>8 | % 66
  <d'' bf'>4 <g'>2 <d'' d'>4 | % 67
  r4 r8 <bf'>8 <ef'>2 ~  | % 68
  <ef'>1 | % 69
  <ef'>8 <bf' g''>8 <f''>8 <ef''>8 <d'' f''>8 <bf'>8 ~  <bf'>4 | % 70
  r8 <bf'>8 ~  <bf'>4 ~  <bf'>4 ~  <bf'>8 <d'>16 <bf'>16 ~  | % 71
  <bf'>4 <d'>8 <bf'>8 ~  <bf'>4 <g' d'>8 <a'>8 | % 72
  r8. <d'>16 ~  <d'>4 ~  <d'>4 ~  <d'>8. <f'>16 | % 73
  r2 <d'>2 ~  | % 74
  <d'>4 <d'>8 <bf'>8 <d''>4 <d'>8 <bf'>8 | % 75
  r2 <g' ef'>2 ~  | % 76
  \tempo 4 = 107
  <g' ef'>4 <ef'>8 <bf'>8 <d''>4 <d'>8 <bf'>8 | % 77
  r1 | % 78
  r2 <f'>8 <a'>8 ~  <a'>4 ~  | % 79
  <a'>1 | % 80
  <bf'>8 <f''>8 <bf''>8 <c'''>8 <f''' c'''>4 <bf'' bf'>4 | % 81
  <ef'>8 <bf'>8 <f''>8 <g''>8 <bf''>2 ~  | % 82
  <bf''>1 | % 83
  r8. <d'>16 ~  <d'>16 <g'>8 <bf'>16 ~  <bf'>16 <d''>8. ~  <d''>16 <bf'>8. ~  | % 84
  <bf'>16 <f' d'>8. ~  <f' d'>8. <bf'>16 ~  <bf'>4 ~  <bf'>8. <a'>16 ~  | % 85
  <a'>1 | % 86
  <f' d' bf'>1 | % 87
  <d'>4 <d'>4 ~  <d'>8 <bf'>8 ~  <bf'>4 | % 88
  <d'' bf'' bf'>1 ~  | % 89
  <d'' bf'' bf'>1 \bar "|." % 90
}

NotesPartZeroStaffOne = {
  \clef "bass"
  \numericTimeSignature \time 4/4
  \key bf \major
  \set fingeringOrientations = #'(down)
  r1 | % 1
  r1 | % 2
  r1 | % 3
  r1 | % 4
  r1 | % 5
  r1 | % 6
  r1 | % 7
  <bf>2 <d>2 | % 8
  <bf ef>1 | % 9
  <bf>1 | % 10
  <g>1 | % 11
  <c' f>1 | % 12
  <c'>1 | % 13
  <g,>8 <d>8 <g>8 <a>8 <bf>4 <bf,>4 | % 14
  r1 | % 15
  r2 <ef>8 <d>8 <g>8 <a>8 | % 16
  <bf>4 <d>4 <f, f>2 | % 17
  r1 | % 18
  r2 <c'>2 | % 19
  r4 <bf>4 <a>8 <c'>8 ~  <c'>4 | % 20
  <g>1 | % 21
  <f>8 <bf>8 <g>8 <f>8 <bf g>4 <d>4 | % 22
  <c f, c'>8 <c'>8 ~  <c'>8 <bf bf,>8 ~  <bf bf,>16 <bf g, bf,>8 <f>16 ~  <f>16 <bf>8. ~  | % 23
  <bf>2 <bf>2 ~  | % 24
  <bf>4 <bf>4 <bf g, g>8 <d>8 <g>8 <a>8 | % 25
  <bf>2 <a g, f>4 ~  <a g, f>8 <g>8 | % 26
  <bf ef bf, g>1 | % 27
  r2 <g,>8 <d>8 <g>8 <a>8 | % 28
  <bf>4 ~  <bf>8 <d>8 <d f d,>2 | % 29
  <ef g bf, ef,>4 ~  <ef g bf, ef,>8 <g>8 <ef>8 <bf>8 ~  <bf>4 ~  | % 30
  <bf>2 <c'>2 ~  | % 31
  <c'>4 <bf>4 <a>8 <c'>8 ~  <c'>4 | % 32
  <g>1 | % 33
  <f>8 <bf>8 ~  <bf>4 ~  <bf>8 <d>8 ~  <d>4 | % 34
  <f, f>8 <c>8 ~  <c>8 <bf bf,>8 ~  <bf bf,>16 <ef ef,>8 <f>16 ~  <f>16 <bf>8. ~  | % 35
  <bf>1 | % 36
  <a,>8 <f>8 ~  <f>4 <ef,>8 <bf,>8 \tuplet 3/2 { <ef>4 <g>8 }| % 37
  <ef>8 <bf>8 ~  <bf>16 <g>8. <bf,>2 | % 38
  <a,>8 <f>8 <a>4 <bf,, bf,>8 <f,>8 <d>8 <f>8 | % 39
  \tuplet 3/2 { <bf>8 <f>8 <bf,>8 }<d>8 <d>16 <f>16 <bf>4 <bf,>4 | % 40
  <ef,>16 <bf,>16 <ef>8 <ef>16 <bf>8 <bf>16 <g>16 <bf,>16 <bf>16 <c'>16 <fs,>16 <d>16 <a>16 <d>16 | % 41
  <g,>16 <d>16 <g>16 <bf>16 ~  <bf>8 <g>16 <d>16 <g>16 <bf>8. \tuplet 3/2 { <f,>8 <f>4 }| % 42
  <ef ef,>16 <bf,>16 <ef>16 <bf>16 <ef>16 <bf>8. ~  <bf>16 <bf>8. <ef>16 <bf>8. | % 43
  <f,>16 <c>16 <f>16 <bf>16 ~  <bf>16 <bf>8 <c>16 <f>16 <c>8 <c'>16 \tuplet 3/2 { <a>8 <c'>4 ~  }| % 44
  <c'>4 <bf>2. | % 45
  r4 <bf>2. | % 46
  r4 <g>2 <d>4 | % 47
  <ef>2 <d>4 <d>4 | % 48
  r2. <d>4 | % 49
  <f, f>2 <c'>2 | % 50
  <c'>8 <a>8 <f>2. | % 51
  <bf,, bf bf,>2 <bf>2 | % 52
  <bf>2 <bf>2 | % 53
  <bf bf, ef,>8 <ef>8 ~  <ef>4 <bf>2 | % 54
  <bf ef>1 | % 55
  <g,>8 <d>8 <g>4 <g>8 <bf>8 ~  <bf>8 <g>8 | % 56
  <f,>8 <c>8 <f>8 <c'>8 <ef,>8 <bf,>8 <ef>8 <g>8 | % 57
  <bf>8 <g>8 ~  <g>8 <bf>8 ~  <bf>8 <g>8 ~  <g>8 <bf>8 | % 58
  <d d,>8 <f>8 ~  <f>8 <bf>8 <ef ef,>8 <ef>8 ~  <ef>8 <bf>8 | % 59
  <ef>8 <bf>8 ~  <bf>4 <ef>8 <bf>8 ~  <bf>8 <bf>8 | % 60
  <d d,>8 <f>8 <bf>4 <f,>8 <f>8 <bf>8. <c'>16 ~  | % 61
  <c'>8 <f>8 ~  <f>16 <bf>8. <c'>4 <f>4 | % 62
  r8. <a>16 <c'>2. | % 63
  <g,>8 <d>8 ~  <d>8 <g>8 <bf>8 <g>8 ~  <g>8 <bf>8 | % 64
  <d d,>4 <d>4 <ef g ef,>8 <bf,>8 <ef>8 <bf>8 ~  | % 65
  <bf>8 <bf>8 ~  <bf>8 <bf>8 <ef>8 <bf>8 ~  <bf>8 <bf>8 | % 66
  <g, g>8 <d>8 <g>8 <g>8 <bf>8 <g>8 ~  <g>8 <bf>8 | % 67
  <d d,>4 <d>4 <ef,>8 <bf,>8 \tuplet 3/2 { <ef>4 <bf>8 }| % 68
  <ef>4 <ef>8 <bf>8 <ef>8 <g>8 <bf>8 <ef>8 | % 69
  <ef>4 <ef>4 <bf>4 <bf>4 | % 70
  <af>2 <g>8 <bf>8 ~  <bf>4 | % 71
  <bf>8 <bf>8 ~  <bf>4 <f>8 <bf>8 ~  <bf>4 | % 72
  <bf>4 <d bf f>4 <c f, c'>8 <bf,>8 <f>8 <c f, f a>8 | % 73
  <bf,>16 <d>8. <bf>2. ~  | % 74
  <bf>8 <g>8 ~  <g>4 ~  <g>8 <bf>8 ~  <bf>4 | % 75
  <ef,>8 <bf,>8 <ef>8 <bf>8 <g>8. <bf ef>16 ~  <bf ef>8. <bf,>16 | % 76
  <bf, ef,>4 <ef>4 <bf, ef,>16 <a>16 <bf>8 ~  <bf>4 | % 77
  <f,>8 <f>8 <d>8 <a>8 <f>8 <bf>8 ~  <bf>4 ~  | % 78
  <bf>8. <c>16 ~  <c>8 <f>8 <a>2 | % 79
  r1 | % 80
  <bf>1 ~  | % 81
  <bf>1 ~  | % 82
  <bf>1 | % 83
  <g>1 ~  | % 84
  <f g>1 | % 85
  <f>1 | % 86
  <bf,>8 <f,>8 <d>8 <bf,>8 <d>8 <f>8 <bf>4 ~  | % 87
  <bf>8 <bf>8 ~  <bf>4 <d>2 | % 88
  r1 | % 89
  r1 \bar "|." % 90
}

LyricsPartZero = \lyricmode {
  \override LyricText.self-alignment-X = #LEFT
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
}

ChordsPartOneStaffZero = \chordmode {
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s2. s8 s8 |
  s4 s8. s16 s4 s8. s16 |
  s1 |
  s2 \tuplet 3/2 { s4 s8 }\tuplet 3/2 { s8 s4 }|
  s2 s4 s8 s8 |
  s1 |
  s2 s2 |
  s2. s4 |
  s1 |
  s2 s4 s8 s8 |
  s4 s4 s4 s8 s8 |
  s1 |
  s2. s8 s8 |
  s4 s4 s4 s8 s16 s16 |
  s1 |
  s2. s16 s16 s8 |
  s4 s4 s4 s8 s8 |
  s1 |
  s4 s8 s8 s4 s4 |
  s1 |
  s2 s2 |
  s8 s8 s4 s2 |
  s2 s8. s16 s16 s8. |
  s4 s8 s8 s2 |
  s4 s8 s8 s8 s8 s4 |
  s2. \tuplet 3/2 { s4 s8 }|
  s2. s4 |
  s16 s8. s4 s4 s16 s8. |
  s2 s2 |
  s8. s16 s4 s4 s8. s16 |
  s1 |
  s2. s4 |
  s2 s2 |
  s2 s2 |
  s1 |
  s2. s4 |
  s1 |
  s8 s8 s8 s8 s4 s8 s8 |
  s1 |
  s4 s4 s4 s8 s8 |
  s1 |
  s2 s2 |
  s2. s4 |
  s4 s8 s8 s2 |
  s1 |
  s2 s2 |
  s2 s2 |
  s1 |
  s4 s8 s8 s4 s4 |
  s4 s8 s8 s2 |
  s1 |
  s4 s8 s8 s4 s4 |
  s4 s8 s16 s16 s2 |
  s1 |
  s8 s8 s8 s8 s4 s4 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s4 s4 s2 |
  s1 |
  s2 s2 |
  s1 |
  s1 |
  s1 |
  s1 |
  s2 s2 |
  s1 |
  s2 s2 |
  s1 |
  s2 s2 |
  s4 s2. |
  s4 s2. |
}

NotesPartOneStaffZero = {
  \clef "treble"
  \numericTimeSignature \time 4/4
  \key bf \major
  \set fingeringOrientations = #'(down)
  r1 | % 1
  r1 | % 2
  r1 | % 3
  r1 | % 4
  r1 | % 5
  r1 | % 6
  r1 | % 7
  r1 | % 8
  r1 | % 9
  r1 | % 10
  r1 | % 11
  r1 | % 12
  r1 | % 13
  r1 | % 14
  r1 | % 15
  r2. <g>8 <a>8 | % 16
  <bf>4 <d'>8. <f'>16 ~  <f'>4 ~  <f'>8. <g' g>16 ~  | % 17
  <g' g>1 | % 18
  <g'>2 \tuplet 3/2 { <g' g''>4 <f' f''>8 ~  }\tuplet 3/2 { <f' f''>8 <ef'' ef'>4 }| % 19
  <f' f''>2 <ef'' ef'>4 ~  <ef'' ef'>8 <d'>8 | % 20
  <d'>1 | % 21
  r2 <f'>2 | % 22
  r2. <d'>4 ~  | % 23
  <d'>1 | % 24
  r2 <bf'>4 <g'>8 <a'>8 | % 25
  <bf'>4 <d'>4 <f'>4 ~  <f'>8 <g'>8 | % 26
  <g'>1 ~  | % 27
  <g'>2. <g'>8 <a'>8 | % 28
  <bf'>4 <d''>4 <f'>4 ~  <f'>8 <ef'>16 <d'>16 | % 29
  <c'>1 ~  | % 30
  <c'>2. <g' g''>16 <f' f''>16 <ef'' ef'>8 | % 31
  <f' f''>4 <bf bf'>4 <ef'' ef'>4 ~  <ef'' ef'>8 <d'>8 | % 32
  <d'>1 ~  | % 33
  <d'>4 <g>8 <a>8 <bf>4 <bf>4 | % 34
  r1 | % 35
  r2 <bf'>2 | % 36
  r8 <f'>8 ~  <f'>4 <g'>2 ~  | % 37
  <g'>2 <a'>8. <bf'>16 ~  <bf'>16 <c'>8. | % 38
  <ef'>4 ~  <ef'>8 <d'>8 <d'>2 ~  | % 39
  <d'>4 ~  <d'>8 <d'>8 ~  <d'>8 <f'>8 ~  <f'>4 | % 40
  <g>2. \tuplet 3/2 { <ef'' ef'>4 <d'' d'>8 }| % 41
  <bf>2. <bf d''>4 | % 42
  r16 <g>8. ~  <g>4 ~  <g>4 ~  <g>16 <d'>8. | % 43
  <bf>2 <a>2 ~  | % 44
  <a>8. <bf>16 ~  <bf>4 ~  <bf>4 ~  <bf>8. <bf''>16 | % 45
  r1 | % 46
  <bf'' f''>2. <f''>4 | % 47
  r2 <bf'>2 | % 48
  <d''>2 <f''>2 | % 49
  r1 | % 50
  r2. <f''>4 | % 51
  <d'>1 | % 52
  <bf>8 <bf>8 <bf bf'>8 <bf bf'>8 <c'>4 ~  <c'>8 <d'>8 | % 53
  <g>1 ~  | % 54
  <g>4 <a>4 <bf>4 ~  <bf>8 <c'>8 | % 55
  <d'>1 | % 56
  <f' a'>2 <bf bf'>2 | % 57
  r2. <bf>4 | % 58
  <f' a'>4 ~  <f' a'>8 <bf'>8 <g'>2 | % 59
  r1 | % 60
  <f'>2 <c'>2 ~  | % 61
  <c'>2 <bf'>2 | % 62
  r1 | % 63
  r4 <g' g''>8 <a'' a'>8 <bf'' bf'>4 <d'' d'>4 | % 64
  <f' f''>4 ~  <f' f''>8 <g'>8 <g'>2 ~  | % 65
  <g'>1 | % 66
  r4 <g'>8 <a'>8 <bf'>4 <d''>4 | % 67
  <f''>4 ~  <f''>8 <ef''>16 <d''>16 <c''>2 ~  | % 68
  <c''>1 ~  | % 69
  <c''>8 <g'>8 <f'>8 <ef'>8 <f'>4 <bf>4 | % 70
  <bf' ef'>1 | % 71
  r1 | % 72
  <bf'>1 | % 73
  <bf>1 ~  | % 74
  <bf>1 | % 75
  <ef'>1 | % 76
  r4 <ef'>4 <a>2 | % 77
  <bf>1 | % 78
  r2 <f'>2 | % 79
  r1 | % 80
  <bf>1 ~  | % 81
  <bf>1 ~  | % 82
  <bf>1 | % 83
  r2 <d''>2 | % 84
  <f'>1 | % 85
  r2 <f'>2 | % 86
  <f' bf d'>1 | % 87
  r2 <bf'>2 | % 88
  r4 <bf'>2. | % 89
  r4 <bf'>2. \bar "|." % 90
}

LyricsPartOne = \lyricmode {
  \override LyricText.self-alignment-X = #LEFT
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
}

ChordsPartTwoStaffZero = \chordmode {
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s4 s8 s8 s4 s4 |
  s8 s16 s16 s2. |
  s2. s8 s8 |
  s4 s4 s2 |
  s1 |
  s2. s8 s8 |
  s4 s4 s4 s8 s8 |
  s1 |
  s8 s8 s8 s8 s4 s4 |
  s4 s8 s8 s8 s8 s4 |
  s1 |
  s2 s4 s8 s8 |
  s4 s4 s4 s8 s8 |
  s1 |
  s1 |
  s2 s4 s8 s16 s16 |
  s1 |
  s1 |
  s4 s4 s4 s8 s8 |
  s1 |
  s4 s8 s8 s4 s4 |
  s4 s8 s8 s2 |
  s1 |
  s8 s8 s4 s2 |
  s2 s8. s16 s16 s8. |
  s4 s8 s8 s2 |
  s2 s2 |
  s2 s16 s16 s16 s16 s8 s8 |
  s2. s4 |
  s2. s4 |
  s2 s2 |
  s8. s16 s4 s4 s8. s16 |
  s4 s4 \tuplet 3/2 { s8 s8 s8 }s16 s16 s16 s16 |
  s2 s4 s4 |
  s2 s2 |
  s1 |
  s1 |
  s2. s4 |
  s1 |
  s8 s8 s4 s4 s8 s8 |
  s1 |
  s4 s4 s4 s8 s8 |
  s1 |
  s2 s2 |
  s2. s4 |
  s2 s2 |
  s1 |
  s2 s2 |
  s1 |
  s1 |
  s16 s8. s4 s4 s16 s8. |
  s2 s2 |
  s1 |
  s1 |
  s2 s2 |
  s1 |
  s4 s8 s8 s4 s4 |
  s4 s8 s8 s2 |
  s2. s8 s8 |
  s4 s4 s4 s8 s8 |
  s1 |
  s1 |
  s1 |
  s4 s4 s2 |
  s1 |
  s1 |
  s1 |
  s2 s2 |
  s1 |
  s1 |
  s2 s2 |
  s8 s8 s4 s8 s8 s4 |
  s1 |
  s1 |
  s2 s2 |
  s4 s2. |
  s4 s2. |
}

NotesPartTwoStaffZero = {
  \clef "bass"
  \numericTimeSignature \time 4/4
  \key bf \major
  \set fingeringOrientations = #'(down)
  r1 | % 1
  r1 | % 2
  r1 | % 3
  r1 | % 4
  r1 | % 5
  r1 | % 6
  r1 | % 7
  r1 | % 8
  r1 | % 9
  r1 | % 10
  r1 | % 11
  r1 | % 12
  r1 | % 13
  r4 <g>8 <a>8 <bf>4 <d'>4 | % 14
  <f>8 <f>16 <g>16 <bf, g>2. ~  | % 15
  <bf, g>2. <g>8 <a>8 | % 16
  <bf>4 <d'>4 <f' f>2 | % 17
  <g>1 | % 18
  r2. <f'>8 <ef'>8 | % 19
  <f'>4 <bf>4 <ef'>4 ~  <ef'>8 <d'>8 | % 20
  <d'>1 | % 21
  <f>8 <bf>8 <g>8 <a>8 <bf>4 <d>4 | % 22
  <c>4 ~  <c>8 <bf,>8 <c a,>8 <f>8 ~  <f>4 ~  | % 23
  <f>1 | % 24
  r2 <bf,>4 <g>8 <a>8 | % 25
  <bf>4 <d'>4 <c'>4 ~  <c'>8 <g>8 | % 26
  <bf, g>1 ~  | % 27
  <bf, g>1 | % 28
  r2 <d>4 ~  <d>8 <ef'>16 <d'>16 | % 29
  <c'>1 | % 30
  r1 | % 31
  r4 <bf>4 <ef'>4 ~  <ef'>8 <d'>8 | % 32
  <d'>1 | % 33
  <f>4 <g>8 <a>8 <bf>4 <d>4 | % 34
  <c>4 ~  <c>8 <bf,>8 <c>2 | % 35
  r1 | % 36
  r8 <f'>8 ~  <f'>4 <g>2 ~  | % 37
  <g>2 <a>8. <bf>16 ~  <bf>16 <c'>8. | % 38
  <ef'>4 ~  <ef'>8 <d'>8 <d'>2 ~  | % 39
  <d'>2 <f>2 | % 40
  <g>2 <a>16 <bf>16 <c'>16 <ef'>16 ~  <ef'>8 <d'>8 | % 41
  <d bf>2. <bf f>4 | % 42
  r2. <ef>4 | % 43
  <bf>2 <a>2 ~  | % 44
  <a>8. <bf>16 ~  <bf>4 ~  <bf>4 ~  <bf>8. <f>16 | % 45
  r4 <ef'>4 \tuplet 3/2 { <ef'>8 <ef'>8 <ef'>8 }<ef'>16 <bf>16 <ef'>16 <ef'>16 | % 46
  r2 <g>4 <d>4 | % 47
  r2 <bf>2 | % 48
  <bf, ef,>1 | % 49
  <f, c' f>1 | % 50
  r2. <f>4 | % 51
  <d bf,>1 | % 52
  <d>8 <d>8 <bf>4 <c'>4 ~  <c'>8 <d'>8 | % 53
  <g>1 ~  | % 54
  <g>4 <a>4 <bf>4 ~  <bf>8 <c'>8 | % 55
  <bf d'>1 | % 56
  <f'>2 <bf>2 | % 57
  r2. <ef,>4 | % 58
  <d>2 <ef bf, ef,>2 ~  | % 59
  <ef bf, ef,>1 | % 60
  <d>2 <f, f>2 | % 61
  r1 | % 62
  r1 | % 63
  r16 <d>8. ~  <d>4 ~  <d>4 ~  <d>16 <d'>8. | % 64
  <d>2 <ef>2 ~  | % 65
  <ef>1 | % 66
  <g,>1 ~  | % 67
  <g,>2 <ef>2 ~  | % 68
  <ef>1 | % 69
  <ef>4 <f'>8 <ef'>8 <f'>4 <bf>4 | % 70
  <af ef'>4 ~  <af ef'>8 <d'>8 <d'>2 ~  | % 71
  <d'>2. <g>8 <a>8 | % 72
  <bf>4 <d>4 <c>4 ~  <c>8 <f, f>8 | % 73
  <g, bf,>1 ~  | % 74
  <g, bf,>1 | % 75
  <ef>1 ~  | % 76
  <ef>4 <ef>4 <ef>2 | % 77
  <f, d bf>1 | % 78
  <a>1 | % 79
  r1 | % 80
  r2 <bf>2 ~  | % 81
  <bf>1 ~  | % 82
  <bf>1 | % 83
  <g>2 <bf,>2 | % 84
  r8 <d'>8 ~  <d'>4 ~  <d'>8 <f>8 ~  <f>4 ~  | % 85
  <f>1 | % 86
  <bf,>1 | % 87
  r2 <bf,>2 | % 88
  r4 <bf,>2. | % 89
  r4 <bf,>2. \bar "|." % 90
}

LyricsPartTwo = \lyricmode {
  \override LyricText.self-alignment-X = #LEFT
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
}

ChordsPartThreeStaffZero = \chordmode {
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s1 |
  s4 s4 s2 |
  s1 |
  s2. s8 s8 |
  s1 |
  s2 s2 |
  s2 s2 |
  s2 s2 |
  s1 |
  s1 |
  s2 s2 |
  s2 s2 |
  s2 s2 |
  s1 |
  s2 s2 |
  s2 s2 |
  s1 |
  s2 s2 |
  s1 |
  s2 s2 |
  s1 |
  s2 s2 |
  s2 s2 |
  s2 s2 |
  s1 |
  s2 s2 |
  s1 |
  s2. s4 |
  s4 s8 s8 s4 s4 |
  s1 |
  s16 s8. s2. |
  s2 s2 |
  s2 s2 |
  s2 s4 s4 |
  s2 s2 |
  s1 |
  s1 |
  s2. s4 |
  s1 |
  s2. s4 |
  s1 |
  s2. s4 |
  s1 |
  s2. s4 |
  s2. s4 |
  s2 s2 |
  s2. s4 |
  s2 s2 |
  s1 |
  s1 |
  s1 |
  s2 s2 |
  s1 |
  s1 |
  s2 s2 |
  s1 |
  s1 |
  s1 |
  s1 |
  s4 s2. |
  s1 |
  s1 |
  s1 |
  s4 s4 s2 |
  s1 |
  s4 s2. |
  s2 s2 |
  s4 s2. |
  s2 s8 s8 s4 |
  s1 |
  s1 |
  s2 s2 |
  s2 s2 |
  s1 |
  s2 s2 |
  s4 s2. |
  s4 s2. |
}

NotesPartThreeStaffZero = {
  \clef "bass_8"
  \numericTimeSignature \time 4/4
  \key bf \major
  \set fingeringOrientations = #'(down)
  r1 | % 1
  r1 | % 2
  r1 | % 3
  r1 | % 4
  r1 | % 5
  r1 | % 6
  r1 | % 7
  r1 | % 8
  r1 | % 9
  r1 | % 10
  r1 | % 11
  r1 | % 12
  r1 | % 13
  r1 | % 14
  r4 <d>4 <ef,>2 ~  | % 15
  <ef,>1 | % 16
  r2. <ef>8 <bf, ef,>8 ~  | % 17
  <bf, ef,>1 | % 18
  r2 <c>2 | % 19
  r2 <a,>2 | % 20
  r2 <bf,>2 | % 21
  r1 | % 22
  <f,>1 | % 23
  r2 <bf,>2 | % 24
  r2 <g,>2 | % 25
  r2 <d a,>2 | % 26
  <ef,,>1 | % 27
  r2 <g,>2 | % 28
  r2 <d>2 | % 29
  <ef,,>1 | % 30
  r2 <ef>2 | % 31
  r1 | % 32
  r2 <bf,>2 | % 33
  r1 | % 34
  r2 <bf,>2 | % 35
  r2 <bf,>2 | % 36
  <a,>2 <ef,>2 ~  | % 37
  <ef,>1 | % 38
  <a,>2 <bf,, bf,>2 ~  | % 39
  <bf,, bf,>1 | % 40
  <ef,>2. <fs,>4 | % 41
  <g,>4 ~  <g,>8 <bf,>8 ~  <bf,>4 <f,>4 | % 42
  <ef,>1 | % 43
  r16 <c>8. <c>2. | % 44
  r2 <bf,>2 | % 45
  r2 <bf,>2 | % 46
  <bf,>2 <bf,>4 <d>4 | % 47
  r2 <bf,>2 | % 48
  <bf, ef,>1 | % 49
  <f,>1 | % 50
  r2. <f,>4 | % 51
  <bf,,>1 | % 52
  r2. <bf,>4 | % 53
  <ef,,>1 | % 54
  r2. <bf,>4 | % 55
  <g,>1 | % 56
  r2. <bf,>4 | % 57
  r2. <bf,>4 | % 58
  <d,>2 <ef,>2 | % 59
  r2. <ef>4 | % 60
  <d,>2 <f,>2 | % 61
  r1 | % 62
  <f,>1 | % 63
  <g,>1 | % 64
  <d>2 <ef>2 ~  | % 65
  <ef>1 | % 66
  <g,>1 | % 67
  <d>2 <ef,>2 ~  | % 68
  <ef,>1 | % 69
  <ef>1 | % 70
  r1 | % 71
  <bf,>1 | % 72
  r4 <d>2. | % 73
  <bf,>1 | % 74
  r1 | % 75
  <bf, ef,>1 | % 76
  <bf,>4 <bf,>4 <bf,>2 | % 77
  <f,>1 | % 78
  r4 <f,>2. | % 79
  r2 <f,>2 | % 80
  <f,>4 <bf,>2. | % 81
  r2 <bf,>8 <bf,>8 ~  <bf,>4 ~  | % 82
  <bf,>1 | % 83
  r1 | % 84
  r2 <bf,>2 | % 85
  r2 <bf,>2 | % 86
  <f,>1 | % 87
  r2 <bf,>2 | % 88
  r4 <bf,>2. | % 89
  r4 <bf,>2. \bar "|." % 90
}

LyricsPartThree = \lyricmode {
  \override LyricText.self-alignment-X = #LEFT
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
  ""1*4/4
}

% The score definition
\score {
  <<
    \new PianoStaff
    \with { instrumentName = "Piano" }
    <<
      \context ChordNames { \ChordsPartZeroStaffZero }
      \new Staff = "1"
      \with { \omit StringNumber } {
        <<
          \context Voice = "NotesPartZeroStaffZero" { \NotesPartZeroStaffZero }
        >>
      }
      \new Staff = "2"
      \with { \omit StringNumber } {
        <<
          \context Voice = "NotesPartZeroStaffOne" { \NotesPartZeroStaffOne }
        >>
      }
    >>
    \new PianoStaff
    \with { instrumentName = "Violin" }
    <<
      \context ChordNames { \ChordsPartOneStaffZero }
      \new Staff = "1"
      \with { \omit StringNumber } {
        <<
          \context Voice = "NotesPartOneStaffZero" { \NotesPartOneStaffZero }
        >>
      }
    >>
    \new PianoStaff
    \with { instrumentName = "Cello" }
    <<
      \context ChordNames { \ChordsPartTwoStaffZero }
      \new Staff = "1"
      \with { \omit StringNumber } {
        <<
          \context Voice = "NotesPartTwoStaffZero" { \NotesPartTwoStaffZero }
        >>
      }
    >>
    \new PianoStaff
    \with { instrumentName = "Double Bass" }
    <<
      \context ChordNames { \ChordsPartThreeStaffZero }
      \new Staff = "1"
      \with { \omit StringNumber } {
        <<
          \context Voice = "NotesPartThreeStaffZero" { \NotesPartThreeStaffZero }
        >>
      }
    >>
  >>
  \layout {
    indent = #32
    \context {
    }
  }
}