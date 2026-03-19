% Scarp_offset_v4g.m
% Adapting for Borah Peak scarp profiles
%
% V4g: preferred variables & fig. now saved (ammended "_preferred"
% V4f: working with saving versions [NOT COMPLETE]
% V4e: adding regression fit values
% V4d: changing output to be min, max, preferred
% V4c: adding option to compile multiple offsets
% V4b: playing around with figure sizing
% V4: Changed slope selection to two-point click per upper/lower slope
% V3: added remove veg. feature
% V2: Added a selection feature...
% V1: Removing diffusion EQs; writing to file
%
% *Modified from far_slope.m  
%
% Input from make_xy.m (optional)
clc
clear all
close all

%Define empty matrices for compiling values
Pname_comb = [];
scarp_off_comb = [];
prof_leng_comb = [];
upper_slope_comb = [];
lower_slope_comb = [];
max_slope_comb = [];
inf_point_comb = [];
pref_ansr_comb = [];
count = [];

%Load profile data
[fn pn] = uigetfile('*.dat;*.txt','Select profile data');
ld_str = ['load ' fn];
eval(ld_str);
ntemp = fn(1:(length(fn) - 4));
assn_str = ['data = ' ntemp ';'];
eval(assn_str);

%loop to allow additional offset measurements
loop = 1; while loop == 1;
close all
clearvars -except ntemp data Pname_comb scarp_off_comb prof_leng_comb ...
    lower_slope_comb upper_slope_comb max_slope_comb inf_point_comb count preferred_scarp_offset pref_ansr_comb

%select inclination data, and subtract 90 (convert to degrees above horizontal)
xp = (data(:,1));
yp = (data(:,2));

%check to make sure profile faces left
l = length(xp);
if xp(1) > xp(l);
    xp = abs(xp-max(xp));  %flip x
end
clear l;

h = xp; h_orig = xp;
e = yp; e_orig = yp;

% call slopeangle_f function to get horiz. dist and slope angles, giving h and e
[dhor, sa] = slopeangle_f (h,e);

get(0,'ScreenSize'); %get screen dimensions
set(0,'Units','pixels');
screen = get(0,'ScreenSize');

%vertical scaling correction (if there are window plot issues)
VS = 0.85;


%figure 1: scarp profile
%************************************

%Figure position: [left bottom width height]
figure('Position', [screen(3)/4 1 screen(3)*(2/3) screen(4)*VS]);

%hf1 = figure(1);
%set(hf1,'name','Scarp profile');
%----------

s1 = subplot (2,1,1);
s_ax = get(s1,'Position');

hold on
plot(dhor,sa,'k:')
plot(dhor,sa,'b.')
%xlabel ('Horizontal distance (m)')
ylabel ('slope (deg)')
%sv = [ min(h) max(h) min(sa)-5 max(sa)+5];
%axis(sv);
axis tight;
grid on;
figure (1)

t1 = subplot (2,1,2);
t_ax = get(t1,'Position');
%set(s1,'Position', [t_ax(1) t_ax(2) s_ax(3) s_ax(4)]);
%title(ntemp)
hold on
plot(xp,yp,'k:'); 
plot(xp,yp,'r.');
%v = [min(xp)-10 max(xp)+10 -10 50]; %axis (v);
axis image
%axis tight; axis equal
grid on;

xlabel ('Horizontal distance (m)')
ylabel ('Vertical distance (m)')
%title name = variable name
%title(ntemp)

clear fn pn ld_str assn_str 

%Query user whether to select subset of data
prompt={'Select subset of profile (1 = yes, 0 = no)?'};
title='Select?';
lineNo = 1;
Def_ans = {'0'};
answer=inputdlg(prompt,title,lineNo,Def_ans);
selct_ansr = (answer{1});
selct_ansr = str2num(selct_ansr);

if selct_ansr == 1;

m1 = ('Click twice to define profile subset');
msg1 = msgbox(m1,'Message'); uiwait(msg1);

figure(1)
% Click to select subset of profile
[xtl ytl] = ginput(1);
[xtu ytu] = ginput(1);    

if xtl > xtu  %check values
    a = xtl;
    b = xtu;
    xtl = b; xtu = a;  %switch values so xtl < xtu
end

for i = 1:length(h);
    if h(i) >= xtl & h(i) <= xtu
        xp2(i) = xp(i);
        yp2(i) = yp(i);
    end
end

close all;

nz = (xp2 > 0); % eliminate values equal to zero
h = xp2(nz);  
e = yp2(nz);

xp = h;
yp = e;

h_orig = xp; %reset orig profile to subset
e_orig = yp;

% call slopeangle_f function to get horiz. dist and slope angles, giving h and e
[dhor, sa] = slopeangle_f (h,e);

figure('Position', [screen(3)/4 1 screen(3)*(2/3) screen(4)*VS]);
%figure 1: scarp profile
%************************************
%hf1 = figure(1);
%set(hf1,'name','Scarp profile');
%----------
subplot 211
hold on
plot(dhor,sa,'k:')
plot(dhor,sa,'b.')
xlabel ('Horizontal distance (m)')
ylabel ('slope (deg)')
sv = [ min(h) max(h) min(sa)-5 max(sa)+5];
axis(sv);
grid on;
figure (1)

subplot 212
%title(ntemp)
hold on
plot(xp,yp,'k:'); 
plot(xp,yp,'r.');
%v = [min(xp)-10 max(xp)+10 -10 50]; %axis (v);
axis image
%axis tight; axis equal
grid on;
xlabel ('Horizontal distance (m)')
ylabel ('Vertical distance (m)')
%title name = variable name
%title(ntemp)

end

%Query user whether to remove parts of profile (e.g., veg)
prompt={'Exclude part of profile (1 = yes, 0 = no)?'};
title='Remove?';
lineNo = 1;
def = {'0'};
answer=inputdlg(prompt,title,lineNo,def);
remov_ansr = (answer{1});
remov_ansr = str2num(remov_ansr);

if remov_ansr == 1;
   
prompt={'How many separate parts to exclude'};
title='Number?';
lineNo = 1;
answer=inputdlg(prompt,title,lineNo);
remov_ansr2 = (answer{1});
remov_ansr2 = str2num(remov_ansr2);

for j = 1:remov_ansr2
    
figure(1)

m1 = ('Click twice to select points to exclude');
msg1 = msgbox(m1,'Message'); uiwait(msg1);

% Click to select part of profile
[xtl ytl] = ginput(1);
[xtu ytu] = ginput(1);    
    
if xtl > xtu  %check values
    a = xtl;
    b = xtu;
    xtl = b; xtu = a;  %switch values so xtl < xtu
end

for i = 1:length(h);
    if h(i) >= xtl & h(i) <= xtu
        xp(i) = 0;
        yp(i) = 0;
    end
end

close all;

nz = (xp > 0); % eliminate values equal to zero
h = xp(nz);  
e = yp(nz);

xp = h;
yp = e;

figure('Position', [screen(3)/4 1 screen(3)*(2/3) screen(4)*VS]);
%figure 1: scarp profile
%************************************
%hf1 = figure(1);
%set(hf1,'name','Scarp profile');
%----------
subplot 211
hold on
plot(dhor,sa,'k:')
plot(dhor,sa,'b.')
xlabel ('Horizontal distance (m)')
ylabel ('slope (deg)')
sv = [ min(h) max(h) min(sa)-5 max(sa)+5];
axis(sv);
grid on;
figure (1)

subplot 212
%title(ntemp)
hold on
plot(h_orig,e_orig,'c.')
plot(xp,yp,'k:'); 
plot(xp,yp,'r.');
%v = [min(xp)-10 max(xp)+10 -10 50]; %axis (v);
%axis([min(xp) max(xp) min(yp) max(yp)]);
axis image
%axis tight; axis equal
grid on;
xlabel ('Horizontal distance (m)')
ylabel ('Vertical distance (m)')
%title name = variable name
%title(ntemp)

end
end

m1 = ('Click twice to select points to use for lower far-field slope');
msg1 = msgbox(m1,'Message'); uiwait(msg1);

figure(1)   

[xtl1 ytl1] = ginput(1);
[xtl2 ytl2] = ginput(1);

m1 = ('Click twice to select points to use for upper far-field slope');
msg1 = msgbox(m1,'Message'); uiwait(msg1);

figure(1)
[xtu1 ytu1] = ginput(1);
[xtu2 ytu2] = ginput(1);

if xtl1 > xtl2  %check lower slope values
    a = xtl1;
    b = xtl2;
    xtl1 = b; xtl2 = a;  %switch values so xtl1 < xtl2
end

if xtu1 > xtu2  %check upper slope values
    a = xtu1;
    b = xtu2;
    xtu1 = b; xtu2 = a;  %switch values so xtl1 < xtl2
end


for i = 1:length(h)
	if h(i) >= xtl1 & h(i) <= xtl2
		lh(i) = h(i); %lower horiz
		le(i) = e(i); %lower elev
	end
end	

for j = 1:length(h)
	if h(j) >= xtu1 & h(j) <= xtu2
		uh(j) = h(j); %upper horiz
		ue(j) = e(j); %loer elev
	end
end

nz = (lh > 0); % eliminate values equal to zero
lh = lh(nz);
le = le(nz);

nz = (uh > 0); % eliminate values equal to zero
uh = uh(nz);  
ue = ue(nz); 

%transform profile data so in columns ascending.
fflh = flipud(rot90(lh)); %lower horiz
ffle = flipud(rot90(le)); %lower elev
ffuh = flipud(rot90(uh)); %upper horiz
ffue = flipud(rot90(ue)); %upper elev

% Linear regression to fit line through upper and lower slope points.
pl = polyfit(fflh,ffle,1);
pu = polyfit(ffuh,ffue,1);

%Evaluate goodness of fit of regression to data
lower_x = fflh; lower_y = ffle;
lower_p = polyfit(lower_x,lower_y,1);
lower_yfit = polyval(lower_p,lower_x);
lower_yresid = lower_y-lower_yfit;
lower_SSresid = sum(lower_yresid.^2);
lower_SStotal = (length(lower_y)-1)*var(lower_y);
lower_rsq = 1-lower_SSresid/lower_SStotal;
lower_RMSE = sqrt(mean((lower_y-lower_yfit).^2));

upper_x = ffuh; upper_y = ffue;
upper_p = polyfit(upper_x,upper_y,1);
upper_yfit = polyval(upper_p,upper_x);
upper_yresid = upper_y-upper_yfit;
upper_SSresid = sum(upper_yresid.^2);
upper_SStotal = (length(upper_y)-1)*var(upper_y);
upper_rsq = 1-upper_SSresid/upper_SStotal;
upper_RMSE = sqrt(mean((upper_y-upper_yfit).^2));

%Determine slope angles
lower_slope = atan(pl(1))*180/pi;
upper_slope = atan(pu(1))*180/pi;

% Extend linear projection beyond scarp face.
ext_dist = (min(ffuh)-max(fflh))/2;

ll = length(fflh);
hlext = fflh(ll) + ext_dist;  %changed from +40/-40 to + 60/-60 
huext = ffuh(1) - ext_dist;

hl = cat(1,fflh,hlext);
hu = cat(1,huext,ffuh);

el = polyval(pl,hl);
eu = polyval(pu,hu);

hold on

plot(hl,el,'bo:');
plot(hu,eu,'bo:');

%plot R^2 and RMSE values
Lrsq = num2str(lower_rsq,'%3.2f');
text(lower_x(length(lower_x)),lower_y(1),Lrsq,'Color','b');
text(lower_x(round(length(lower_x)/2)),lower_y(1),'R^2','Color','b');

Ursq = num2str(upper_rsq,'%3.2f');
text(upper_x(length(upper_x)),upper_y(1),Ursq,'Color','b');
text(upper_x(round(length(upper_x)/2)),upper_y(1),'R^2','Color','b');

Lrmse = num2str(lower_RMSE,'%3.2f');
text(lower_x(round(length(lower_x)/2)),lower_y(length(lower_y)),Lrmse,'Color','m');
text(lower_x(1),lower_y(length(lower_y)),'RMSE','Color','m');

Urmse = num2str(upper_RMSE,'%3.2f');
text(upper_x(round(length(upper_x)/2)),upper_y(length(upper_y)),Urmse,'Color','m');
text(upper_x(1),upper_y(length(upper_y)),'RMSE','Color','m');

%Determine number of profile points used
Lower_prof_pts = length(lower_x);
Upper_prof_pts = length(upper_x);

%{
plot(xp,(yp+10),'r');
plot(xp,(yp+10),'kx');
%}
zoom on

% Determine max slope of the scarp face.
% max_slope.m  adapted from sciday.m by Ann Matson 11/24/02
figure(1)

m1 = ('Click twice to select points to use for scarp slope');
msg1 = msgbox(m1,'Message'); uiwait(msg1);

[mxl,myl] = ginput(1);
[mxu,myu] = ginput(1);

if mxl > mxu  %check values
    a = mxl;
    b = mxu;
    mxl = b; mxu = a;  %switch values so mxl < mxu
end

for k =1:length(h)
	if h(k) >= mxl & h(k) <= mxu
		slpx(k) = h(k);
		slpy(k) = e(k);
	end
end

tf2 = (slpx > 0); % elminate zeros from data.
mx = slpx(tf2);
my = slpy(tf2);

ps = polyfit(mx,my,1); % calculate max slope.

max_slope = atan(ps(1))*180/pi;

% vert_offset.m  adapted from sciday.m by Ann Matson 11/24/02
% Calculate scarp offset and inflection point.
% Find the intersection between the far field slope lines and
% max slope line.

figure(1)

int_el = (ps(2)*pl(1)-pl(2)*ps(1))/(pl(1)-ps(1));
int_hl = (int_el-ps(2))/ps(1);

int_eu = (ps(2)*pu(1)-pu(2)*ps(1))/(pu(1)-ps(1));
int_hu = (int_eu-ps(2))/ps(1);

int_e = [int_el int_eu];
int_h = [int_hl int_hu];
plot(int_h,int_e,'go--')
scarp_ht = int_eu-int_el;

inflection_point = (int_hl+int_hu)/2;

au = polyval(pu,inflection_point);
al = polyval(pl,inflection_point);

scarp_offset = au - al; % calculate scarp offset

ax = [inflection_point inflection_point];
ay = [al au];

plot(ax,ay,'r-','LineWidth',1.5)

%Shift data to inflection point

hs = h-inflection_point;
es = e-polyval(ps,inflection_point);

%plot offset on figure
plot_x = min(h); plot_y = max(e);

%text(plot_x, plot_y,'File name:','FontSize',10);
plot_str = ['Profile: ' ntemp];
text(plot_x, plot_y,plot_str); 

plot_y2 = plot_y-((max(e)-min(e))/4);
%text(inflection_point+.01, ax,'(m):','FontSize',10);
str1 = num2str(scarp_offset,'%3.2f'); 
text(inflection_point+((au-al)/2), min(ay),str1,'Color','r','FontSize',11);

%{
plot_y2 = plot_y-((max(e)-min(e))/4);
text(plot_x, plot_y2,'Vertical offset (m):','FontSize',10);
str1 = num2str(scarp_offset,'%3.2f'); 
text(plot_x+10,plot_y2,str1);
%}

%clear mxl myl mxu myu k slpx slpy tf2 mx my %int_el int_hl int_eu
%clear int_hu int_e int_h au al ax ay

%calc profile length
%profile_length = abs(max(xp) - min(xp)); previous method - which is total
%profile, not points selected
profile_length = max([xtu2; xtu1])-min([xtl1; xtl2]);

%Query user whether to include results in compilation
%*********************************************
prompt={'Include results? (1 = yes, 0 = no)'};
title='Compile?';
lineNo = 1;
def = {'1'};
answer=inputdlg(prompt,title,lineNo,def);
compile_ansr = (answer{1});
compile_ansr = str2num(compile_ansr);

if compile_ansr == 1;
    
%*********************************************
%Output valariable values to screen:
%clc

%fprintf('\n')
%fprintf('Inflection point (meters): %3.2f',inflection_point');
%fprintf('\n')
%fprintf('\n')
%fprintf('Vertical scarp height (meters): %3.2f',scarp_ht');
%fprintf('\n\n')

    
%prompt user to name profile version
prompt={'Profile version (numeric; ie., 2):'};
title='Name';
lineNo = 1;
%def = {'1'};
def = {num2str(sum(count)+1)};
answer=inputdlg(prompt,title,lineNo,def);
Pname = (answer{1});

%Query user whether measurement is preferred value
prompt={'Is this your preferred offset? (1 = yes, 0 = no)'};
title='Preferred?';
lineNo = 1;
def = {'0'};
answer=inputdlg(prompt,title,lineNo,def);
preferred_ansr = (answer{1});
preferred_ansr = str2num(preferred_ansr);

if preferred_ansr == 1;
    
    preferred_scarp_offset = scarp_offset;
    
    str_p = [ntemp '_preferred_var.mat'];
    save_str_p = ['save ' str_p];
    eval(save_str_p);
    
    h_pref = gcf;
    str_fig = ['savefig(h_pref,''' ntemp '_preferred.fig'')'];
    eval(str_fig);

end

%fprintf('\n')
fprintf('\n')
fprintf('Profile: %s',ntemp');

fprintf(', version: %s',Pname');
fprintf('\n')
%fprintf('\n')
fprintf('Scarp Offset (meters): %3.2f',scarp_offset');
fprintf('\n')
%fprintf('\n')
fprintf('Profile length (meters): %3.2f',profile_length');
fprintf('\n')
%fprintf('\n')
fprintf('Lower far-field slope (degrees): %3.2f',lower_slope');
fprintf('\n')
%fprintf('\n')
fprintf('Upper far-field slope (degrees): %3.2f',upper_slope');
fprintf('\n')
%fprintf('\n')
fprintf('Scarp slope (degrees): %3.2f',max_slope');
fprintf('\n')
fprintf('Preferred offset? (1=yes, 0=no): %3.0f',preferred_ansr);
fprintf('\n')
fprintf('\n')
fprintf('Regression Statistics:');
fprintf('\n')
fprintf('Number of lower-surface points: %3.0f',Lower_prof_pts);
fprintf('\n')
fprintf('R^2 for lower-surface regression: %3.2f',lower_rsq);
fprintf('\n')
fprintf('RMSE for lower-surface regression: %3.2f',lower_RMSE);
fprintf('\n')
fprintf('Number of upper-surface points: %3.0f',Upper_prof_pts);
fprintf('\n')
fprintf('R^2 for upper-surface regression: %3.2f',upper_rsq);
fprintf('\n')
fprintf('RMSE for upper-surface regression: %3.2f',lower_RMSE);
fprintf('\n')

%Plot Pname on figure
ver_str = num2str(Pname);
ver_str = ['Version: ' ver_str];
text(min(h), max(e)-((max(e)-min(e))/10),ver_str);

%{
plot_y3 = plot_y-((max(e)-min(e))/2);
text(plot_x, plot_y3,'Saved: Profile version','FontSize',10);
text(plot_x+5, plot_y3,Pname); 
%}

%Compile values
Pname_comb = [Pname_comb Pname];
scarp_off_comb = [scarp_off_comb scarp_offset];
prof_leng_comb = [prof_leng_comb profile_length];
lower_slope_comb = [lower_slope_comb lower_slope];
upper_slope_comb = [upper_slope_comb upper_slope];
max_slope_comb = [max_slope_comb max_slope];
%inf_point_comb = [inf_point_comb inflection_point];
pref_ansr_comb = [pref_ansr_comb preferred_ansr];
count = [count 1];

end

%Query user to loop back
prompt={'Re-run offset measurement (1 = yes, 0 = no)?'};
title='Re-run?';
lineNo = 1;
Def_ans = {'1'};
answer=inputdlg(prompt,title,lineNo,Def_ans);
loop = (answer{1});
loop = str2num(loop);

end

%Query user whether to save
%*********************************************
prompt={'Save results? (1 = yes, 0 = no)'};
title='Save?';
lineNo = 1;
def = {'1'};
answer=inputdlg(prompt,title,lineNo,def);
save_ansr = (answer{1});

save_ansr = str2num(save_ansr);

if save_ansr == 1;

%prompt user to name profile
prompt={'Text to be appended to file name (ie. ver2):'};
title='Save';
lineNo = 1;
def = {'1'};
answer=inputdlg(prompt,title,lineNo,def);
Sname = (answer{1});

%prompt user to select preferred, mean, or midpoint
prompt={'Use preferred (1), mean (2), or midpoint (3)?'};
title='Summary displacement?';
lineNo = 1;
def = {'1'};
answer=inputdlg(prompt,title,lineNo,def);
sum_ansr = (answer{1});

sum_ansr = str2num(sum_ansr);

if sum_ansr == 1;
    scarp_off_sum = preferred_scarp_offset;
    
elseif sum_ansr == 2;
    scarp_off_sum = mean(scarp_off_comb);
    
elseif sum_ansr == 3;
    scarp_off_min = min(scarp_off_comb);
    scarp_off_max = max(scarp_off_comb);
    scarp_off_sum = (scarp_off_max+scarp_off_min)/2;
end

%Pname_mn = mean(Pname_comb);
scarp_off_min = min(scarp_off_comb);
scarp_off_max = max(scarp_off_comb);

prof_leng_mn = mean(prof_leng_comb);
upper_slope_mn = mean(upper_slope_comb);
lower_slope_mn = mean(lower_slope_comb);
max_slope_mn = mean(max_slope_comb);
inf_point_mn = mean(inf_point_comb);
profile_runs = sum(count);

%not using STD for now
%{
%Pname_std = std(Pname_comb);
scarp_off_std = std(scarp_off_comb);
prof_leng_std = std(prof_leng_comb);
upper_slope_std = std(upper_slope_comb);
lower_slope_std = std(lower_slope_comb);
max_slope_std = std(max_slope_comb);
inf_point_std = std(inf_point_comb);
%}
%{
a = [scarp_off_sum; prof_leng_mn; lower_slope_mn; upper_slope_mn; max_slope_mn; inf_point_mn; profile_runs];
b = [scarp_off_std; prof_leng_std; lower_slope_std; upper_slope_std; max_slope_std; inf_point_std; 0];
P_sum = [a b];

str2 = [ntemp '_mean_' Sname];
save_str = ['save ' str2 '.txt ' '-ascii ' 'P_sum'];
eval(save_str);


c = scarp_off_comb; 
d = prof_leng_comb; 
e = lower_slope_comb; 
f = upper_slope_comb; 
g = max_slope_comb; 
h  = inf_point_comb;

P_indiv = [c; d; e; f; g; h];

str3 = [ntemp '_indiv_' Sname];
save_str = ['save ' str3 '.txt ' '-ascii ' 'P_indiv'];
eval(save_str);
%}

%save summary and mean values
a = [scarp_off_sum; scarp_off_min; scarp_off_max; prof_leng_mn; lower_slope_mn; ...
    upper_slope_mn; max_slope_mn; profile_runs];

str2 = [ntemp '_' Sname '-summary'];
save_str = ['save ' str2 '.txt ' '-ascii ' 'a'];
eval(save_str);

%save all individual offset values
c = scarp_off_comb; 
d = prof_leng_comb; 
e = lower_slope_comb; 
f = upper_slope_comb; 
g = max_slope_comb; 
h = pref_ansr_comb;

P_indiv = [c; d; e; f; g; h];

str3 = [ntemp '_' Sname '-individual'];
save_str = ['save ' str3 '.txt ' '-ascii ' 'P_indiv'];
eval(save_str);


end

fprintf('\n')
fprintf('Data file name: %s',ntemp');
fprintf('\n')
if save_ansr == 1;
fprintf('Saved data name: %s',Sname');
fprintf('\n')
end

if sum_ansr == 1; %preferred
fprintf('Summary scarp offset (meters): %3.2f',scarp_off_sum');
fprintf('\n')
    
elseif sum_ansr == 2; %mean
fprintf('Mean scarp offset (meters): %3.2f',scarp_off_sum');
fprintf('\n')
    
elseif sum_ansr == 3; %midpoint
fprintf('Midpoint scarp offset (meters): %3.2f',scarp_off_sum');
fprintf('\n')
end

fprintf('Minimum scarp offset (meters): %3.2f',scarp_off_min');
fprintf('\n')
fprintf('Maximum scarp offset (meters): %3.2f',scarp_off_max');
fprintf('\n')
fprintf('Mean profile length (meters): %3.2f',prof_leng_mn');
fprintf('\n')
fprintf('Mean lower far-field slope (degrees): %3.2f',lower_slope_mn');
fprintf('\n')
fprintf('Mean upper far-field slope (degrees): %3.2f',upper_slope_mn');
fprintf('\n')
fprintf('Mean scarp slope (degrees): %3.2f',max_slope_mn');
fprintf('\n')
fprintf('Number of iterations: %3.0f',sum(count)');
fprintf('\n')



