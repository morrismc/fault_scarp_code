% slopeangle_f.m
% for use with X,Y or (h,e) - 2dimensional profile data
% dhor = horiz. distance for slope points, sa = slope angles
% call as:
%
% [dhor,sa] = slopeangle_f(h,e)


function [dhor, sa] = slopeangle_f(h,e)

de = diff(e);
dd = diff(h);
sa = atan(de./dd)*180/pi;
 
for i = 1:length(h)-1
dhor(i) = ((h(i+1)-h(i))/2)+h(i);
end


% 6/18/03 by C. DuRoss to compare profile data to slope data
% adapted for use as a function on 12/15/03