function [ output_args ] = spectral_domain_partition( intensor, invector, outfile, small )
%SPECTRAL_DOMAIN_PARTITION Decomposes pdb structure from distance matrix
%into domain definitions, using the logistic similarity function.
%
%   intensor - input file with distance tensor to read
%   invector - input file with weight vector to read
%   outfile - output file to print results in
%   small - a small number to consider as 0 (helping us find the fiedler
%           vector)
    
    small = str2num(small);
    %Read the data
    %fprintf('Reading input\n');
    % Read the input tensor
    disttensor = readtensor(intensor);
    % Read the input vector
    weightvector = dlmread(invector);
    % This below need to be redefined; we only read distances, so the
    % following part needs to be converting the distances tensor read to a
    % similarity matrix, using the optimal cutoff given the average
    % similarity matrix... You get my drift...
    dists = get_distances( positions );
    %Get the optimal similarity function parameter
    %fprintf('getting similarity sigma\n');
    similarity_sigma = getcutoff( 0, max(max(dists)), 0.001, @entropy_logistic, dists );
    [ similarity_sigma, m ] = get_binary_topology_cutoff( dists, similarity_sigma );
    fprintf('Sigma: %.2f\nNo. Clusters: %d\n', similarity_sigma, m);
    %Form the laplacian
    %fprintf('getting laplacian\n');
    laplacian = getlaplacian( dists, @sim_logistic, similarity_sigma );
    %Do the decomposition and select the fiedler vector
    [U, S, V] = svd(laplacian);
    fiedler = select_component( U, S, small );
    %Filter the component
    seqdists = get_distances_sequential( dists );
    filtered = filter_logistic_sequential( fiedler, seqdists );
    %Partition where there are least density over the fiedler vector
    domains = fiedler_partition_ttest( filtered, 1/length(filtered) );
    %fprintf('printing results\n');
    dlmwrite(outfile, [[1:length(domains)]', domains + 1], '\t');
end

% Following functions are just copy pasted from the domains repository in
% order of appearance in the main function of this file (above)

%% I N P U T
%%%%%%%%%%%%

function [ t ] = readtensor( infile )
%READTENSOR Reads a tensor from a (L*N)xL matrix on file
%   infile - tensor infile
%   t - reshaped tensor returned
%   
%   Expects all graphs part of the (L*N)xL matrix to be transposed, so that
%   transposing before reshaping actually reshapes them in the correct
%   pose.
    t = dlmread(infile);
    s = size(t);
    t = reshape(t', [s(2) s(2) S(1)/S(2)]);
end

%% C U T O F F - S E A R C H
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ x ] = getcutoff( minimum, maximum, tol, fun, data )
%GETCUTOFF_GAUSSIAN Summary of this function goes here
%   Detailed explanation goes here
    resphi = 2 - ((1 + sqrt(5)) / 2);
    a = minimum;
    b = a + resphi * (maximum - minimum);
    c = maximum;
    fa = fun(a, data);
    fb = fun(b, data);
    fc = fun(c, data);
    x = getcutoff_recursive(a, b, c, fa, fb, fc, tol, resphi, fun, data);
end

function [ x ] = getcutoff_recursive( x1, x2, x3, f1, f2, f3, t, p, fun, data )
%GETCUTOFF Summary of this function goes here
%   Detailed explanation goes here
    %fprintf('getcutoff_recursive, x1=%0.2f x2=%0.2f x3=%0.2f\n', x1, x2, x3);
    if (x3 - x2 > x2 - x1)
        %new probe point is between x2 and x3
        x = x2 + p * (x3 - x2);
        if(abs(x3 - x1) < t * (abs(x2) + abs(x)))
        x = (x3 + x1)/2;
        return;
        end
        fx = fun(x, data);
        if(fx == f2)
            x = (x3 + x1)/2;
            return;
        end
        if(fx < f2)
            % x1 is outside new interval
            x = getcutoff_recursive(x2, x, x3, f2, fx, f3, t, p, fun, data);
            return;
        else
            % x3 is outside new interval
            x = getcutoff_recursive(x1, x2, x, f1, f2, fx, t, p, fun, data);
            return;
        end
    else
        %new probe point is between x1 and x2
        x = x2 - p * (x2 - x1);
        if(abs(x3 - x1) < t * (abs(x2) + abs(x)))
            x = (x3 + x1)/2;
            return;
        end
        fx = fun(x, data);
        if(fx == f2)
            x = (x3 + x1)/2;
            return;
        end
        if(fx < f2)
            % x3 is outside new interval
            x = getcutoff_recursive(x1, x, x2, f1, fx, f2, t, p, fun, data);
            return;
        else
            % x1 is outside new interval
            x = getcutoff_recursive(x, x2, x3, fx, f2, f3, t, p, fun, data);
            return;
        end
    end
end

function [ s, m ] = get_binary_topology_cutoff( dst, s1 )
%GET_BINARY_TOPOLOGY_CUTOFF Summary of this function goes here
%   Detailed explanation goes here
    
    s = s1;
    step = (s1 - 5.0) / 50;
    minimum = step + 5.0;
    T = sum(sim_logistic(dst, s), 2);
    m = length(topology_local_maximum_exhaustive(T, dst, s));
    while m < 2 && s > minimum
        s = s - step;
        T = sum(sim_logistic(dst, s), 2);
        m = length(topology_local_maximum_exhaustive(T, dst, s));
    end
end

function [ P ] = sim_logistic( data, sigma )
%SIM_LOGISTIC Summary of this function goes here
%   Detailed explanation goes here

    P = 1 ./ (ones(size(data)) + exp(data - (sigma .* ones(size(data)))));
end

function [ M ] = topology_local_maximum_exhaustive( T, dst, s )
%TOPOLOGY_LOCAL_MAXIMUM Summary of this function goes here
%   Detailed explanation goes here
    
    M = [];
    for node = 1:length(T)
        local_weights = sim_logistic(dst(:,node), s);
        local_topology = local_weights .* T;
        [Y, I] = max(local_topology);
        if I == node
            M = [M; node];
        end
    end
end

%% S V D
%%%%%%%%

function [ L, P, T ] = getlaplacian( data, fun, sigma )
%GETLAPLACIAN Returns the normalized random walk laplacian
%   Detailed explanation goes here
    P = fun(data, sigma);
    T = diag(sum(P, 2));
    L = eye(size(P)) - T\P;
end

function [ c ] = select_component( U, S, small )
%SELECT_COMPONENT Returns smallest nonzero singular component
%   Detailed explanation goes here

    i = 1;
    l = size(S, 1);
    while S(end-i, end-i) <= small && i < l-1
        i = i+1;
    end
    fprintf('cutoff=%f, component=%d\n', small, i);
    c = U(:, end-i);
end


%% F I L T E R I N G
%%%%%%%%%%%%%%%%%%%%
function [ seqdists ] = get_distances_sequential( dists )
%GET_DISTANCES_SEQUENTIAL Summary of this function goes here
%   Detailed explanation goes here

    seqdists = zeros(size(dists));
    %accumulate first row
    for i = 2:size(seqdists, 1)
        seqdists(1, i) = seqdists(1, i-1) + dists(i, i-1);
    end
    %mirror first row
    seqdists(2:end, 1) = seqdists(1, 2:end)';
    for i = 2:size(seqdists, 1)
        %subtract distance from previous residue from future distances
        seqdists(i, i+1:end) = seqdists(i-1, i+1:end) - seqdists(i, i-1);
        %mirror
        seqdists(i+1:end, i) = seqdists(i, i+1:end)';
    end
end

function [ d, s, m, h ] = filter_logistic_sequential( data, dists )
%FILTER_LOGISTIC_SEQUENTIAL Scan for the first peak in the entropy
%   Detailed explanation goes here

    %meandist = get_meandist_sequential(dists);
    meandist = get_mediandist_sequential(dists);
    x = [1:floor(max(max(dists)) / meandist)];
    h = zeros(length(x),1);
    ndata = normalize_data(data);
    maxent = 0;
    for j = x
        h(j) = entropy_logistic_sequence(j * meandist, ndata, dists);
        if maxent < h(j)
            maxent = h(j);
        else
            break;
        end
    end
    s = (j - 1) * meandist;
    m = h(j - 1);
    d = sim_logistic_sequence(ndata, dists, s);
    d = normalize_data(d);
end

function [ mediandist ] = get_mediandist_sequential( dists )
%GET_MEANDIST_SEQUENTIAL Summary of this function goes here
%   Detailed explanation goes here

    pairdists = zeros(size(dists, 1) - 1, 1);
    for i = 2:size(dists, 1)
        pairdists(i - 1) = dists(i, i-1);
    end
    mediandist = median(pairdists);
end

function [ ndata ] = normalize_data( data )
%NORMALIZE_DATA Summary of this function goes here
%   Detailed explanation goes here

    ndata = (data - mean(data)) ./ std(data);
end

function [ h ] = entropy_logistic_sequence( sigma, data, dists )
%ENTROPY_LOGISTIC_MDIM Summary of this function goes here
%   Detailed explanation goes here
    
%     dists = abs((ones(size(data)) * [1:size(data, 1)]) - ((ones(size(data)) * [1:size(data, 1)])'));
%     e = abs(ones(size(data)) * data') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists))))));
%     p = sum(e, 2);
%     p = p./sum(p);
%     h = - p' *  log(p);
    %ndata = data - sum(data)/length(data);
    ndata = normalize_data(data);
    %dists = abs((ones(size(ndata)) * [1:size(ndata, 1)]) - ((ones(size(ndata)) * [1:size(ndata, 1)])'));
    e = abs(ones(size(ndata)) * ndata') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists))))));
    p = sum(e, 2);
    p = p./sum(p);
    h = - p' *  log(p);
end

function [ P ] = sim_logistic_sequence( data, dists, sigma )
%SIM_LOGISTIC Summary of this function goes here
%   Detailed explanation goes here

    
    %dists = abs((ones(size(data)) * [1:size(data, 1)]) - ((ones(size(data)) * [1:size(data, 1)])'));
    %P = sum((ones(size(data)) * data') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists)))))), 2);
    %P = sum((ones(size(data)) * data') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists)))))), 2) ./ length(data);
    %P = sum((ones(size(data)) * data') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists)))))), 2);
    ndata = normalize_data(data);
    %dists = abs((ones(size(ndata)) * [1:size(ndata, 1)]) - ((ones(size(ndata)) * [1:size(ndata, 1)])'));
    P = (ones(size(ndata)) * ndata') ./ (ones(size(dists)) + exp(abs(dists - (sigma .* ones(size(dists))))));
    P = sum(P, 2);
end

%% P A R T I T I O N I N G
%%%%%%%%%%%%%%%%%%%%%%%%%%

function [ d, tf, I, fI] = fiedler_partition_ttest( fiedler, alpha )
%FIEDLER_PARTITION Summary of this function goes here
%   Detailed explanation goes here

    %Sweep the entropies
    [ s, h ] = topology_plot_entropy( fiedler );
    %Choose the minimum entropy sigma and induce corresponding topology
    [ hm, i ] = min(h);
    sm = s(i);
    [ t ] = topology_induce( fiedler, sm );
    
    %Get the sorted local minima in the induced topology
    local_minima = topology_sort_local_minima(fiedler, t);
    
    %search for first local minima that separate partitions from parent graph
    for i = 1:length(local_minima)
        current = local_minima(i);
        tf = fiedler(current);
        d = fiedler <= fiedler(current);
        %end search when both hypothesis are dismissed
        if ttest2(fiedler, fiedler(d), 'alpha', alpha) && ttest2(fiedler, fiedler(~d), 'alpha', alpha)
            break;
        end
    end
    I = current;
    
    %check which fiedler index this is
    [y, ind] = sort(fiedler);
    fI = 1;
    while fiedler(ind(fI)) < tf
        fI = fI + 1;
    end
end

function [ s, h ] = topology_plot_entropy( fiedler )
%TOPOLOGY_PLOT_ENTROPY Summary of this function goes here
%   Detailed explanation goes here

    s = [1:1:50]';
    h = zeros(size(s));
    for i = 1:length(s);
        t = topology_induce( fiedler, s(i) );
        h(i) = topology_entropy( t );
    end
end

function [ topology ] = topology_induce( data, sigma )
%TOPOLOGY_INDUCE Summary of this function goes here
%   Detailed explanation goes here

    %Scale and center (scaling is most important)
    %Get all pairwise distances over the fiedler vector
    
    %working, good filtering and with reasonable resizing
    ndata = normalize_data(data) * 2 * nthroot(((length(data) * 3) / (4 * pi)), 3);
    distances = get_distances(ndata);
    topology = 1 ./ (ones(size(distances)) + exp(distances - sigma * ones(size(distances))));
    topology = sum(topology, 2);
    
%     ndata = normalize_data(data) * sqrt(length(data));%nthroot(length(data),3);
%     distances = get_distances(ndata);
%     topology = 1 ./ exp(distances ./ sigma);
%     topology = sum(topology, 2);

    %Works OK, with OK filtering, but entropy is of no guidance. Why...?
%     distances = get_distances(data);
%     maxdist = max(max(distances));
%     topology = 1 ./ (ones(size(distances)) + exp(((50/maxdist) * distances) - sigma * ones(size(distances))));
%     topology = sum(topology, 2);
    
    %Try with the gaussian, Works, OK, but still no entropy guidance
%     distances = get_distances(data);
%     maxdist = max(max(distances));
%     topology = 1 ./ exp(((50/maxdist) * distances) ./ sigma);
%     topology = sum(topology, 2);

    %what happens when we use the absolute? We get the same bullshit as in
    %the sequential filter...
%     distances = get_distances(data);
%     maxdist = max(max(distances));
%     topology = 1 ./ (ones(size(distances)) + exp(abs(((50/maxdist) * distances) - sigma * ones(size(distances)))));
%     topology = sum(topology, 2);

    %Induce the topology field
    %topology = 1 ./ (ones(size(distances)) + exp(distances - sigma * ones(size(distances))));
    %topology = 1 ./ (ones(size(distances)) + exp(((50/maxdist) .* distances) - sigma * ones(size(distances))));
    %topology = 1 ./ exp(distances ./ sigma);
    %Calculate the topology density in each node
    %topology = sum(topology, 2);
end

function [ dists ] = get_distances( positions )
%GET_DISTANCES Summary of this function goes here
%   Detailed explanation goes here
    
    dists = zeros(size(positions, 1));
    for i = 1:size(positions, 2)
        dists = dists + ((ones(size(positions(:, i))) * positions(:, i)') - ((ones(size(positions(:, i))) * positions(:, i)')')).^2;
    end
    dists = sqrt(dists);
end

function [ h ] = topology_entropy( topology )
%TOPOLOGY_ENTROPY Summary of this function goes here
%   Detailed explanation goes here

    p = topology ./ sum(sum(topology));
    h = - p' * log(p);
end

function [ sorted_minima ] = topology_sort_local_minima( fiedler, topology )
%TOPOLOGY_SORT_LOCAL_MINIMA Summary of this function goes here
%   Detailed explanation goes here

    is_minimum = zeros(size(topology));
    [y, I] = sort(topology);
    for i = 1:length(I);
        j = I(i);
        %don't check the start and end of topology (since it cannot be a
        %minimum)
        if j > 1 && j < length(topology)
            %if this is a minimum
            if topology(j - 1) > topology(j) && topology(j + 1) > topology(j)
                is_minimum(i) = 1;
            end
        end
    end
    %return indexes of local minimums, starting with the lowest
    sorted_minima = I(is_minimum == 1);
end

